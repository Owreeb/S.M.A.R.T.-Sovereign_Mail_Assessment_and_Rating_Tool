"""
Fills in the email domain for each organisation.

The rule is (only for orgs that don't have an email domain yet):
- If an organisation already has a current smtp_in mail system, we don't
  crawl. We just use the website domain as the email domain.

The result always goes into org_domain_history with the history logic, so a
new version is only made when the email domain actually changed.
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
    """
    Pull emails out of href values.
    """
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
    """
    Domain of the first non-generic email, or None.
    """
    for email in emails:
        if is_generic(email):
            continue
        return email.split("@", 1)[1].lower()
    return None


def find_impressum_link(response) -> str | None:
    """
    First <a> that looks like an Impressum/Kontakt link (http(s) only).
    """
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
        """
        Args:
            rows: List of (org_id, website) we want to scrape.
            results: A dict we fill with {org_id: email_domain}. The caller
                reads it after the crawl is done.
        """
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

        # nothing on the homepage -> try the Impressum
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
        # ignore errors
        pass

    def _extract_domain_mailto(self, response) -> str | None:
        """Grab mailto: links from the page."""
        hrefs = response.css('a[href^="mailto:"]::attr(href)').getall()
        return pick_email_domain(extract_emails(hrefs))


def _orgs_with_mx(session) -> set:
    """
    Gets the ids of all orgs that have a current smtp_in mail system.

    Args:
        session: The session.

    Returns:
        A set of organisation ids.
    """
    stmt = (
        select(OrgMailSystemHistory.organisation_id)
        .join(MailSystem, MailSystem.id == OrgMailSystemHistory.mail_system_id)
        .where(OrgMailSystemHistory.is_current.is_(True))
        .where(MailSystem.role == MailSystemRole.SMTP_IN)
        .distinct()
    )
    return set(session.scalars(stmt).all())


def _set_email_domain(session, run, row, email_domain) -> None:
    """
    Writes the email domain into the org domain history.

    It uses update_history, so website and website_domain stay the same and a
    new version is only made if the email domain really changed.

    Args:
        session: The session.
        run: The current ScannerRun.
        row: The current OrgDomainHistory row of the org.
        email_domain: The email domain we want to set.
    """
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
    """
    Crawls the given websites and collects the email domains.

    The results are kept in a dict.

    Args:
        work: List of (org_id, website) tuples to scrape.

    Returns:
        dict {org_id: email_domain}.
    """
    results: dict = {}
    process = CrawlerProcess()
    process.crawl(MailtoSpider, rows=work, results=results)
    process.start()  # blocks until the crawl is finished
    return results


def run_scraper(session, run) -> None:
    """
    Fills in the email domain for orgs that don't have one yet.

    Orgs that already have an email domain are skipped. For the rest: orgs
    with an smtp_in just get website_domain as their email domain, orgs
    without an MX get their website crawled.

    Args:
        session: The session to write with.
        run: The current ScannerRun (shared with the rest of the pipeline).
    """
    # only orgs that don't have an email domain yet
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
            # has an smtp_in -> email domain is just the website domain
            if row.website_domain:
                _set_email_domain(session, run, row, row.website_domain)
        elif website and website.strip():
            # no MX -> crawl the website
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
