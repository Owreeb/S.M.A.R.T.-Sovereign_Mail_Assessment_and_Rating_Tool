"""
Scrapes the email domain for each org in `bronze_table`.

For each row with a website but no email: open the homepage, look for
mailto: links, take the first non-generic one and store its domain.
If nothing there, follow an Impressum/Kontakt link and try again.
Plain-text emails in the body are ignored on purpose (too noisy).
"""

import multiprocessing
import re
import sqlite3
from typing import Iterable
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess

BATCH_SIZE = 500

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

    def __init__(
        self,
        rows: list[tuple[str, str]],
        db_path: str,
        table: str,
    ) -> None:
        super().__init__()
        self.rows = rows
        self.db_path = db_path
        self.table = table
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    async def start(self):
        for row_id, website in self.rows:
            url = normalize_url(website)
            if not url:
                continue
            yield scrapy.Request(
                url=url,
                meta={"row_id": row_id, "stage": "homepage"},
                callback=self.parse,
                dont_filter=True,
                errback=self.errback,
            )

    def parse(self, response):
        row_id = response.meta["row_id"]
        stage = response.meta.get("stage")

        domain = self._extract_domain_mailto(response)
        if domain:
            self._save(row_id, domain)
            return

        # nothing on the homepage -> try the Impressum
        if stage == "homepage":
            impressum_url = find_impressum_link(response)
            if impressum_url:
                yield scrapy.Request(
                    url=impressum_url,
                    meta={"row_id": row_id, "stage": "impressum"},
                    callback=self.parse,
                    dont_filter=True,
                    errback=self.errback,
                )

    def errback(self, failure):
        # ignore timeouts/DNS/HTTP errors, just move on
        pass

    def _extract_domain_mailto(self, response) -> str | None:
        """Grab mailto: links from the page."""
        hrefs = response.css('a[href^="mailto:"]::attr(href)').getall()
        return pick_email_domain(extract_emails(hrefs))

    def _save(self, row_id, email_domain: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            UPDATE {self.table}
            SET email = ?
            WHERE id = ?
              AND (email IS NULL OR TRIM(email) = '')
            """,
            (email_domain, row_id),
        )
        self.conn.commit()

    def closed(self, reason):
        self.conn.close()


def count_rows(db_path: str, table: str) -> int:
    """
    How many rows still need scraping (have website, no email yet).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE website IS NOT NULL AND TRIM(website) <> ''
          AND (email IS NULL OR TRIM(email) = '')
        """
    )
    result = cursor.fetchone()[0]
    conn.close()
    return result


def fetch_rows(
    db_path: str,
    table: str,
    batch_size: int,
    last_rowid: int,
) -> list[tuple[str, str]]:
    """
    Next batch of rows to scrape, paged by ROWID. Returns (id, website)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, website
        FROM {table}
        WHERE website IS NOT NULL AND TRIM(website) <> ''
          AND (email IS NULL OR TRIM(email) = '')
          AND ROWID > ?
        ORDER BY ROWID
        LIMIT ?
        """,
        (last_rowid, batch_size),
    )
    rows = [(row["id"], row["website"]) for row in cursor.fetchall()]
    conn.close()
    return rows


def _peek_batch_end_rowid(
    db_path: str, table: str, last_rowid: int, batch_size: int
) -> int | None:
    """
    Max ROWID of the next batch (None if nothing left).

    The subprocess can't tell us where it stopped, so we look it up here.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT MAX(rid) FROM (
            SELECT ROWID AS rid FROM {table}
            WHERE website IS NOT NULL AND TRIM(website) <> ''
              AND (email IS NULL OR TRIM(email) = '')
              AND ROWID > ?
            ORDER BY ROWID
            LIMIT ?
        )
        """,
        (last_rowid, batch_size),
    )
    result = cursor.fetchone()[0]
    conn.close()
    return result


def _run_single_batch(db_path: str, table: str, batch_size: int, last_rowid: int) -> None:
    """
    One scrapy batch in this process (subprocess entry point).
    """
    rows = fetch_rows(db_path, table, batch_size=batch_size, last_rowid=last_rowid)
    if not rows:
        return
    process = CrawlerProcess()
    process.crawl(MailtoSpider, rows=rows, db_path=db_path, table=table)
    process.start()


def run_scraper(db_path: str, table: str, batch_size: int = BATCH_SIZE) -> None:
    """
    Run the scraper in batches, one fresh process per batch (clean reactor + FD pool).

    Pagination uses SQLite's ROWID as cursor.
    Rows that fail stay NULL and are skipped because the next batch starts past them.
    """
    remaining = count_rows(db_path, table)
    if remaining == 0:
        print("No rows with website found that still need an email.")
        return

    print(f"Scraping {remaining} websites in batches of {batch_size}...")
    last_rowid = 0
    batch_num = 0
    while True:
        batch_end_rowid = _peek_batch_end_rowid(db_path, table, last_rowid, batch_size)
        if batch_end_rowid is None:
            break
        batch_num += 1
        print(f"  Batch {batch_num} (rowids {last_rowid + 1}..{batch_end_rowid})...")
        proc = multiprocessing.Process(
            target=_run_single_batch,
            args=(db_path, table, batch_size, last_rowid),
        )
        proc.start()
        proc.join()
        last_rowid = batch_end_rowid

    print(f"Scraping complete. Processed up to ROWID {last_rowid}.")
