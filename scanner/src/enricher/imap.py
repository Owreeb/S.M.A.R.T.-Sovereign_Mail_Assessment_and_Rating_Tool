"""
scan_mail_servers.py
--------------------
For each unique domain in `email` and `website_domain` columns, probes common
mail-server hostnames (IMAP / POP3 / SMTP) and tries to read a protocol
greeting within 1 second. Results are written back to the original DataFrame
and saved as a CSV.

Usage:
    python scan_mail_servers.py
"""

import asyncio
import sqlite3
import pandas as pd

# ── configuration ────────────────────────────────────────────────────────────
DB_PATH    = (
    "/home/julian/Projects/"
    "S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/"
    "scanner/database/raw_data.db"
)
TABLE      = "bronze_table"
OUTPUT_CSV = "mail_server_scan_results.csv"
TIMEOUT    = 1.0        # seconds to wait for a greeting banner
MAX_CONC   = 30         # max simultaneous coroutines

# Candidate subdomain → port pairs to probe per domain
CANDIDATES: list[tuple[str, int, str]] = [
    # (subdomain_prefix, port, protocol_label)
    ("imap",      143, "IMAP"),
    ("imap",      993, "IMAPS"),
    ("mail",      143, "IMAP"),
    ("mail",      993, "IMAPS"),
    ("mail",      110, "POP3"),
    ("mail",      995, "POP3S"),
    ("mail",       25, "SMTP"),
    ("mail",      587, "SMTP-STARTTLS"),
    ("mail",      465, "SMTPS"),
    ("pop3",      110, "POP3"),
    ("pop3",      995, "POP3S"),
    ("pop",       110, "POP3"),
    ("pop",       995, "POP3S"),
    ("smtp",       25, "SMTP"),
    ("smtp",      587, "SMTP-STARTTLS"),
    ("smtp",      465, "SMTPS"),
    ("webmail",   143, "IMAP"),
    ("webmail",   110, "POP3"),
    ("exchange",  143, "IMAP"),
    ("exchange",   25, "SMTP"),
    ("mx",         25, "SMTP"),
    ("mx1",        25, "SMTP"),
]
# ─────────────────────────────────────────────────────────────────────────────


async def probe(host: str, port: int, protocol: str,
                sem: asyncio.Semaphore) -> dict | None:
    """
    Open a TCP connection to host:port and try to read at least one byte
    (the protocol greeting) within TIMEOUT seconds.
    Returns a result dict on success, None on failure.
    """
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=TIMEOUT,
            )
            # Read up to 1024 bytes of the greeting banner
            banner = await asyncio.wait_for(reader.read(1024), timeout=TIMEOUT)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return {
                "host":     host,
                "port":     port,
                "protocol": protocol,
                "banner":   banner.decode(errors="replace").strip()[:200],
            }
        except Exception:
            return None


async def scan_domain(domain: str, sem: asyncio.Semaphore) -> dict | None:
    """
    Fire all candidate probes for *domain* concurrently and return the
    first successful result (or None if none respond).
    """
    domain = domain.strip().lower()
    if not domain:
        return None

    tasks = [
        probe(f"{prefix}.{domain}", port, proto, sem)
        for prefix, port, proto in CANDIDATES
    ]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            # Cancel the rest to free up connections quickly
            return result
    return None


async def scan_domains(domains: list[str]) -> dict[str, dict | None]:
    """Scan every domain in *domains*, honouring MAX_CONC."""
    sem = asyncio.Semaphore(MAX_CONC)
    tasks = {domain: scan_domain(domain, sem) for domain in domains}
    results: dict[str, dict | None] = {}
    coros = {domain: asyncio.create_task(coro)
             for domain, coro in tasks.items()}
    done = await asyncio.gather(*coros.values(), return_exceptions=True)
    for domain, result in zip(coros.keys(), done):
        results[domain] = result if not isinstance(result, Exception) else None
    return results


def extract_domain(value: str) -> str:
    """Pull the bare domain from an e-mail address or URL."""
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    # e-mail address
    if "@" in value:
        return value.split("@")[-1]
    # strip common URL cruft
    for prefix in ("https://", "http://", "www."):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.split("/")[0]


def apply_results(df: pd.DataFrame, col: str,
                  results: dict[str, dict | None]) -> pd.DataFrame:
    """Add three columns to df based on scan results for *col*."""
    domain_col = f"_domain_{col}"
    df[domain_col] = df[col].apply(extract_domain)

    df[f"{col}_mail_server"]       = df[domain_col].map(
        lambda d: results.get(d, {}).get("host")    if results.get(d) else None
    )
    df[f"{col}_mail_port"]         = df[domain_col].map(
        lambda d: results.get(d, {}).get("port")    if results.get(d) else None
    )
    df[f"{col}_mail_protocol"]     = df[domain_col].map(
        lambda d: results.get(d, {}).get("protocol") if results.get(d) else None
    )
    df[f"{col}_mail_banner"]       = df[domain_col].map(
        lambda d: results.get(d, {}).get("banner")  if results.get(d) else None
    )

    df.drop(columns=[domain_col], inplace=True)
    return df


async def main() -> None:
    # ── load data ─────────────────────────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(f"SELECT * FROM {TABLE} WHERE {TABLE}.email IS NOT NULL", conn)
    conn.close()
    print(f"Loaded {len(df):,} rows from '{TABLE}'.")

    for source_col in ("email", "website_domain"):
        if source_col not in df.columns:
            print(f"  Column '{source_col}' not found – skipping.")
            continue

        # ── unique domains ─────────────────────────────────────────────────
        domains = list({
            extract_domain(v) for v in df[source_col] if extract_domain(v)
        })
        print(f"\n[{source_col}] {len(domains):,} unique domains to scan …")

        # ── async scan ────────────────────────────────────────────────────
        results = await scan_domains(domains)
        found   = sum(1 for v in results.values() if v)
        print(f"[{source_col}] Found mail servers for {found}/{len(domains)} domains.")

        # ── write back to df ──────────────────────────────────────────────
        df = apply_results(df, source_col, results)

    # ── save ──────────────────────────────────────────────────────────────────
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResults saved to '{OUTPUT_CSV}'.")


if __name__ == "__main__":
    asyncio.run(main())

