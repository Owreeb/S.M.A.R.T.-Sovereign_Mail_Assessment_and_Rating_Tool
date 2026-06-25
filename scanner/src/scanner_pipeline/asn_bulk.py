"""
Bulk ASN / country enrichment for IP addresses via Team Cymru's WHOIS service.

The per-IP DNS lookups in the ASN scan step get rate-limited by Team Cymru on
large runs, so a full scan ends up with most IPs missing their ASN/country.
This module uses the bulk WHOIS interface (whois.cymru.com:43), which is built
for looking up thousands of IPs in a single connection, and updates the
ip_addresses rows (asn, asn_org, country_code) plus the derived country_rating
and asn_rating (hoster rating).

Run as a one-off recovery after a full scan, e.g.:

    from src.db.base import make_engine, make_session
    from src.scanner_pipeline.asn_bulk import enrich_ip_addresses
    from src.json_dumper.dump import write_dump

    engine = make_engine("database/SMART.db")
    with make_session(engine)() as session:
        enrich_ip_addresses(session, only_missing=False)
        write_dump(session)
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
    Look up ASN, country and AS name for many IPs via Team Cymru bulk WHOIS.

    Args:
        ips: the IP addresses to look up.
        timeout: socket timeout in seconds.

    Returns:
        A map ip -> {"asn": int|None, "asn_org": str|None, "country_code": str|None}.
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
            # A network/socket failure must not abort the whole scan: the IPs in
            # this batch just stay without ASN data (graceful degradation, same
            # as a per-IP DNS failure in the old step).
            print(f"ASN bulk lookup failed for a batch of {len(batch)} IPs: {exc}")
            continue

        for line in buf.decode(errors="replace").splitlines():
            if "|" not in line or line.lower().startswith("bulk mode"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            asn_raw, ip, _prefix, cc, _reg, _alloc, asname = parts[:7]
            # origin can be "NA" or "1234 5678" -> take the first number
            first = asn_raw.split()[0] if asn_raw and asn_raw != "NA" else None
            result[ip] = {
                "asn": int(first) if first and first.isdigit() else None,
                "asn_org": asname if asname and asname != "NA" else None,
                "country_code": cc if cc and cc != "NA" else None,
            }
    return result


def enrich_ip_addresses(session: Session, only_missing: bool = True) -> int:
    """
    Enrich ip_addresses rows with ASN/country and the derived ratings.

    Args:
        session: the DB session.
        only_missing: if True, only look up rows that have no asn_org yet.

    Returns:
        How many rows were updated.
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
