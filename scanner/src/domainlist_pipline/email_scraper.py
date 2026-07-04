"""
fill in the email domain for orgs that don't have one yet.

orgs with a current smtp_in reuse their website domain instead of getting
crawled. everything goes through the history logic, so a new version only lands
when the email domain actually changed.
"""

import re
from typing import Iterable
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess
from sqlalchemy import select

from src.db import (
    MailSystem,
    MailSystemRole,
    Organisation,
    OrgDomainHistory,
    OrgMailSystemHistory,
    update_history,
)

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)

GENERIC_LOCAL_PARTS = {
    "noreply",
    "no-reply",
    "webmaster",
    "postmaster",
    "admin",
    "hostmaster",
    "mailer-daemon",
}

IMPRESSUM_KEYWORDS = ("impressum", "kontakt")


def normalize_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        return raw_url
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        return f"https://{raw_url}"
    return raw_url


def extract_emails(hrefs: Iterable[str]) -> list[str]:
    """pull emails out of href values"""
    emails: list[str] = []
    for href in hrefs:
        if not href:
            continue
        value = href
        if value.lower().startswith("mailto:"):
            value = value.split(":", 1)[1]
        value = value.split("?", 1)[0]
        value = value.split("#", 1)[0]
        for match in EMAIL_PATTERN.findall(value):
            if match not in emails:
                emails.append(match)
    return emails


def is_generic(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    return local in GENERIC_LOCAL_PARTS


def pick_email_domain(emails: Iterable[str]) -> str | None:
    """domain of the first non-generic email, or None"""
    for email in emails:
        if is_generic(email):
            continue
        return email.split("@", 1)[1].lower()
    return None


def find_impressum_link(response) -> str | None:
    """first <a> that looks like an impressum/kontakt link, http(s) only"""
    for anchor in response.css("a"):
        href = (anchor.attrib.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        text = " ".join(anchor.css("::text").getall()).lower()
        haystack = f"{href.lower()} {text}"
        if not any(keyword in haystack for keyword in IMPRESSUM_KEYWORDS):
            continue
        absolute = response.urljoin(href)
        if absolute.startswith(("http://", "https://")):
            return absolute
    return None


class MailtoSpider(scrapy.Spider):
    name = "mailto_spider"

    custom_settings = {
        "DOWNLOAD_TIMEOUT": 12,
        "LOG_LEVEL": "CRITICAL",
        "RETRY_TIMES": 1,
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "REACTOR_THREADPOOL_MAXSIZE": 20,
        "DOWNLOAD_DELAY": 0.5,
        "DNS_TIMEOUT": 10,
        "LOG_FORMATTER": "scrapy.logformatter.LogFormatter",
        "USER_AGENT": "SMART-BOT/1.4",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        },
    }

    def __init__(self, rows: list[tuple], results: dict) -> None:
        # results gets filled with {org_id: email_domain}, caller reads it after the crawl
        super().__init__()
        self.rows = rows
        self.results = results

    async def start(self):
        for org_id, website in self.rows:
            url = normalize_url(website)
            if not url:
                continue
            yield scrapy.Request(
                url=url,
                meta={"org_id": org_id, "stage": "homepage"},
                callback=self.parse,
                dont_filter=True,
                errback=self.errback,
            )

    def parse(self, response):
        org_id = response.meta["org_id"]
        stage = response.meta.get("stage")

        domain = self._extract_domain_mailto(response)
        if domain:
            self.results[org_id] = domain
            return

        # nothing on the homepage, try the impressum
        if stage == "homepage":
            impressum_url = find_impressum_link(response)
            if impressum_url:
                yield scrapy.Request(
                    url=impressum_url,
                    meta={"org_id": org_id, "stage": "impressum"},
                    callback=self.parse,
                    dont_filter=True,
                    errback=self.errback,
                )

    def errback(self, failure):
        pass

    def _extract_domain_mailto(self, response) -> str | None:
        """grab mailto: links off the page"""
        hrefs = response.css('a[href^="mailto:"]::attr(href)').getall()
        return pick_email_domain(extract_emails(hrefs))


def _orgs_with_mx(session) -> set:
    """org ids that have a current smtp_in mail system"""
    stmt = (
        select(OrgMailSystemHistory.organisation_id)
        .join(MailSystem, MailSystem.id == OrgMailSystemHistory.mail_system_id)
        .where(OrgMailSystemHistory.is_current.is_(True))
        .where(MailSystem.role == MailSystemRole.SMTP_IN)
        .distinct()
    )
    return set(session.scalars(stmt).all())


def _set_email_domain(session, run, row, email_domain) -> None:
    """write email_domain into the domain history, keep website_domain as-is"""
    update_history(
        session,
        OrgDomainHistory,
        run,
        match={"organisation_id": row.organisation_id},
        tracked={
            "email_domain": email_domain,
            "website_domain": row.website_domain,
        },
    )


def _scrape_email_domains(work: list[tuple]) -> dict:
    """crawl the given (org_id, website) pairs -> {org_id: email_domain}"""
    results: dict = {}
    process = CrawlerProcess()
    process.crawl(MailtoSpider, rows=work, results=results)
    process.start()  # blocks until the crawl is done
    return results


def run_scraper(session, run) -> None:
    """fill in email domains: smtp_in orgs reuse website_domain, the rest get crawled"""
    candidates = session.execute(
        select(OrgDomainHistory, Organisation.website)
        .join(Organisation, Organisation.id == OrgDomainHistory.organisation_id)
        .where(
            OrgDomainHistory.is_current.is_(True),
            (OrgDomainHistory.email_domain.is_(None))
            | (OrgDomainHistory.email_domain == ""),
        )
    ).all()

    mx_orgs = _orgs_with_mx(session)

    to_scrape = []
    for row, website in candidates:
        if row.organisation_id in mx_orgs:
            # has smtp_in, so email domain = website domain
            if row.website_domain:
                _set_email_domain(session, run, row, row.website_domain)
        elif website and website.strip():
            to_scrape.append((row, website))

    session.commit()

    if not to_scrape:
        print("Nothing to scrape.")
        return

    print(f"Scraping {len(to_scrape)} websites...")
    results = _scrape_email_domains(
        [(row.organisation_id, website) for row, website in to_scrape]
    )

    for row, _ in to_scrape:
        email_domain = results.get(row.organisation_id)
        if email_domain:
            _set_email_domain(session, run, row, email_domain)
    session.commit()
    print(f"Scraping complete. Found {len(results)} email domains.")
