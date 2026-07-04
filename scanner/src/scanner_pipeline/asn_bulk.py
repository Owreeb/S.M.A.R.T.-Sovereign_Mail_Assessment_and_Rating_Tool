"""
bulk asn/country enrichment for ip addresses via team cymru's whois.

per-ip dns lookups get rate-limited on big runs, so most ips end up without
asn/country. this uses the bulk whois interface (whois.cymru.com:43) to look up
thousands of ips per connection and fills in asn/asn_org/country_code plus the
derived country_rating and asn_rating. run as a one-off recovery after a scan.
"""

from __future__ import annotations

import socket

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import IpAddress, VendorCountryRating, derive_hoster_rating

CYMRU_HOST = "whois.cymru.com"
CYMRU_PORT = 43
BATCH_SIZE = 1000


def lookup_asn_bulk(ips: list[str], timeout: float = 30.0) -> dict[str, dict]:
    """
    bulk-lookup asn/country/as-name for many ips.

    returns ip -> {"asn", "asn_org", "country_code"}.
    """
    result: dict[str, dict] = {}
    for start in range(0, len(ips), BATCH_SIZE):
        batch = ips[start:start + BATCH_SIZE]
        payload = "begin\nverbose\n" + "\n".join(batch) + "\nend\n"

        try:
            sock = socket.create_connection((CYMRU_HOST, CYMRU_PORT), timeout=timeout)
            try:
                sock.sendall(payload.encode())
                buf = b""
                while True:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    buf += chunk
            finally:
                sock.close()
        except OSError as exc:
            # socket died, don't kill the scan; this batch just goes without
            # asn data
            print(f"ASN bulk lookup failed for a batch of {len(batch)} IPs: {exc}")
            continue

        for line in buf.decode(errors="replace").splitlines():
            if "|" not in line or line.lower().startswith("bulk mode"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            asn_raw, ip, _prefix, cc, _reg, _alloc, asname = parts[:7]
            # origin can be "NA" or "1234 5678", take the first number
            first = asn_raw.split()[0] if asn_raw and asn_raw != "NA" else None
            result[ip] = {
                "asn": int(first) if first and first.isdigit() else None,
                "asn_org": asname if asname and asname != "NA" else None,
                "country_code": cc if cc and cc != "NA" else None,
            }
    return result


def enrich_ip_addresses(session: Session, only_missing: bool = True) -> int:
    """
    enrich ip_addresses rows with asn/country and derived ratings.

    only_missing skips rows that already have an asn_org. returns rows updated.
    """
    stmt = select(IpAddress)
    if only_missing:
        stmt = stmt.where(IpAddress.asn_org.is_(None))
    rows = list(session.scalars(stmt))
    if not rows:
        return 0

    by_ip = {row.ip_address: row for row in rows}
    looked_up = lookup_asn_bulk(list(by_ip))

    updated = 0
    for ip, row in by_ip.items():
        info = looked_up.get(ip)
        if not info:
            continue
        row.asn = info["asn"]
        row.asn_org = info["asn_org"]
        row.country_code = info["country_code"]
        if info["country_code"]:
            try:
                row.country_rating = int(
                    VendorCountryRating.from_country_code(info["country_code"])
                )
            except Exception:
                pass
        hoster = derive_hoster_rating(info["country_code"], info["asn_org"])
        if hoster is not None:
            row.asn_rating = hoster
        updated += 1

    session.commit()
    return updated
