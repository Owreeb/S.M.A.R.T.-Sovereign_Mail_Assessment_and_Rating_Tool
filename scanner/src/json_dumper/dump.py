"""
Dump the current state of the database into the frontend JSON format.

The sovereignty_index is calculated on the fly while dumping, following
the Souveränitätsindex V2 specification (see sovereignty_index_calc.py).
"""
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import brotli

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import (
    IpAddress,
    MailSystem,
    MailSystemIpHistory,
    MailSystemRole,
    OrgDomainHistory,
    OrgMailSystemHistory,
    Organisation,
    ScannerRun,
)
from src.json_dumper.sovereignty_index_calc import (
    compute_average_index,
    compute_sovereignty_index,
)

EXPORT_ROLES = [
    MailSystemRole.SMTP_OUT,
    MailSystemRole.SMTP_IN,
    MailSystemRole.IMAP_POP3,
    MailSystemRole.WEBMAILER,
]


def _current_ips(
    session: Session, mail_system: MailSystem, org_id
) -> list[IpAddress]:
    """
    Get the IPs that are currently behind a mail system for one organisation.

    Args:
        session: The database session.
        mail_system: The mail system to look up.
        org_id: The organisation the IPs must belong to (the link is scoped to
            org + mail system, since mail systems are shared across orgs).

    Returns:
        The current IpAddress rows of this org's mail system.
    """
    return list(
        session.scalars(
            select(IpAddress)
            .join(MailSystemIpHistory, MailSystemIpHistory.ip_address_id == IpAddress.id)
            .where(
                MailSystemIpHistory.mail_system_id == mail_system.id,
                MailSystemIpHistory.organisation_id == org_id,
                MailSystemIpHistory.is_current.is_(True),
            )
        )
    )


def _serialize_ip(ip: IpAddress) -> dict[str, Any]:
    """Turn an IpAddress row into the JSON dict for export."""
    return {
        "ip_address": ip.ip_address,
        "rdns_hostname": ip.rdns_hostname,
        "country_code": ip.country_code,
        "country_rating": ip.country_rating,
        "hoster": ip.asn_org,
        "hoster_rating": ip.asn_rating,
    }


def _serialize_mail_system(
    session: Session, mail_system: MailSystem, proxy: MailSystem | None, org_id
) -> dict[str, Any]:
    """
    Turn a mail system (plus optional proxy) into the JSON dict.

    Args:
        session: The database session.
        mail_system: The main mail system.
        proxy: The proxy in front of it, or None.
        org_id: The organisation whose IPs to attach.

    Returns:
        The mail system dict in the export format.
    """
    entry: dict[str, Any] = {
        "software": mail_system.software,
        "open_source_rating": mail_system.open_source_rating,
        "vendor": mail_system.vendor,
        "vendor_country": mail_system.vendor_country,
        "vendor_country_rating": mail_system.vendor_country_rating,
        "vendor_category": mail_system.vendor_category,
        "vendor_category_rating": mail_system.vendor_category_rating,
        "ips": [_serialize_ip(ip) for ip in _current_ips(session, mail_system, org_id)],
    }
    if proxy is not None:
        proxy_entry = _serialize_mail_system(session, proxy, None, org_id)
        del proxy_entry["proxy"]
        entry["proxy"] = proxy_entry
    else:
        entry["proxy"] = None
    return entry


def _last_checked(session: Session, run_ids: set) -> str | None:
    """
    Get the newest timestamp of the runs the current rows came from.

    Args:
        session: The database session.
        run_ids: The valid_from_run ids of the org's current history rows.

    Returns:
        The newest finished_at (or started_at)
    """
    if not run_ids:
        return None
    runs = session.scalars(select(ScannerRun).where(ScannerRun.id.in_(run_ids)))
    timestamps = [run.finished_at or run.started_at for run in runs]
    timestamps = [ts for ts in timestamps if ts is not None]
    if not timestamps:
        return None
    # SQLite stores naive timestamps, but a freshly created in-memory run can
    # still be tz-aware; normalize so old and new runs stay comparable.
    timestamps = [ts.replace(tzinfo=None) for ts in timestamps]
    return max(timestamps).isoformat()


def _slim_system(system: dict[str, Any]) -> dict[str, Any]:
    """
    Slim a serialized mail system for the export.

    The per-IP objects (raw IP, rDNS, repeated ratings) are the bulk of the
    file and not interesting on their own, so they are dropped in favour of the
    distinct host countries and hosters. Everything else (software, vendor,
    ratings, proxy) is kept.

    Args:
        system: A full serialized mail system dict.

    Returns:
        The slimmed system dict.
    """
    ips = system.get("ips") or []
    proxy = system.get("proxy")
    return {
        "software": system.get("software"),
        "vendor": system.get("vendor"),
        "vendor_country": system.get("vendor_country"),
        "vendor_country_rating": system.get("vendor_country_rating"),
        "vendor_category": system.get("vendor_category"),
        "vendor_category_rating": system.get("vendor_category_rating"),
        "open_source_rating": system.get("open_source_rating"),
        "countries": sorted({ip["country_code"] for ip in ips if ip.get("country_code")}),
        "hosters": sorted({ip["hoster"] for ip in ips if ip.get("hoster")}),
        "proxy": _slim_system(proxy) if proxy else None,
    }


def _serialize_org(session: Session, org: Organisation) -> dict[str, Any]:
    """
    Turn an organisation into a JSON dict

    Args:
        session: The database session.
        org: The organisation to serialize.

    Returns:
        The organisation dict in the export format
    """
    domain_row = session.scalars(
        select(OrgDomainHistory).where(
            OrgDomainHistory.organisation_id == org.id,
            OrgDomainHistory.is_current.is_(True),
        )
    ).first()

    system_rows = list(
        session.scalars(
            select(OrgMailSystemHistory).where(
                OrgMailSystemHistory.organisation_id == org.id,
                OrgMailSystemHistory.is_current.is_(True),
            )
        )
    )

    mail_systems: dict[str, list[dict[str, Any]]] = {
        role.value: [] for role in EXPORT_ROLES
    }
    providers: list[str] = []
    hosters: list[str] = []

    for row in system_rows:
        ms = row.mail_system
        # a standalone proxy is the visible inbound path -> score it as smtp_in
        export_role = (
            MailSystemRole.SMTP_IN if ms.role == MailSystemRole.PROXY else ms.role
        )
        if export_role not in EXPORT_ROLES:
            continue
        mail_systems[export_role.value].append(
            _serialize_mail_system(session, ms, row.proxy_system, org.id)
        )
        if ms.vendor and ms.vendor not in providers:
            providers.append(ms.vendor)
        for ip in _current_ips(session, ms, org.id):
            if ip.asn_org and ip.asn_org not in hosters:
                hosters.append(ip.asn_org)

    run_ids = {row.valid_from_run for row in system_rows}
    if domain_row is not None:
        run_ids.add(domain_row.valid_from_run)

    # score from the full structure, then slim it for the output
    sovereignty_index = compute_sovereignty_index(mail_systems)
    slim_mail_systems = {
        role: [_slim_system(system) for system in systems]
        for role, systems in mail_systems.items()
    }

    # the org's primary domain (website), falling back to the email domain
    domain = None
    if domain_row is not None:
        domain = domain_row.website_domain or domain_row.email_domain

    return {
        "org": org.name,
        "domain": domain,
        "email_domain": domain_row.email_domain if domain_row else None,
        "category": org.category_tag,
        "wikidata_url": org.wikidata_url,
        "city": org.city,
        "state": org.state,
        "country": org.country,
        "lat": org.latitude,
        "long": org.longitude,
        "last_checked": _last_checked(session, run_ids),
        "sovereignty_index": sovereignty_index,
        "providers": providers,
        "hosters": hosters,
        "mail_systems": slim_mail_systems,
    }

def _top_shares(
    data: list[dict[str, Any]], key: str, limit: int = 10
) -> list[dict[str, Any]]:
    """
    Count how often each name appears in the orgs' lists under ``key``.

    Args:
        data: The serialized org dicts.
        key: The list field to count -> "providers" or "hosters".
        limit: How many top entries to return.

    Returns:
        A list of {"name": ..., "share": ...} dicts, sorted by share.
    """
    counter: Counter = Counter()
    for org in data:
        for name in org.get(key) or []:
            counter[name] += 1
    total = sum(counter.values())
    if total == 0:
        return []
    return [
        {"name": name, "share": round(count / total, 2)}
        for name, count in counter.most_common(limit)
    ]


def _build_overview(data: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build the overview object for the overview file.

    Args:
        data: The serialized org dicts.

    Returns:
        The overview json with the average sovereignty index and the
        top mail vendors, hosters
    """
    average, _ = compute_average_index(data)
    domains = {org["email_domain"] for org in data if org.get("email_domain")}
    return {
        "overview": {
            "orgsScanned": len(data),
            "domainsScanned": len(domains),
            "sovereigntyIndex": average,
        },
        "topMailVendors": _top_shares(data, "providers"),
        "topHosters": _top_shares(data, "hosters"),
    }


def _write_json_with_brotli(data: Any, path: Path) -> None:
    """
    Write data as JSON and a compressed Brotli version of it.

    Args:
        data: The JSON-serializable data to write.
        path: The path of the plain .json file.
    """
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(payload, encoding="utf-8")
    compressed = brotli.compress(payload.encode("utf-8"))
    path.with_suffix(path.suffix + ".br").write_bytes(compressed)


def _export_output_path(session: Session) -> Path:
    """
    Build the export path next to the database the session is bound to.

    Args:
        session: The database session.

    Returns:
        The path for the export fgolder
    """
    db_file = session.get_bind().url.database
    return Path(db_file).resolve().parent / "export" / "organizations.json"


def write_dump(session: Session) -> int:
    """
    Dump all organisations and write them as JSON next to the database.

    Writes two files into <db folder>/export: organizations.json
    with all orgs and a date-named overview file (e.g. 2026-06-12.json)
    with the average sovereignty index and the top vendors/hosters.

    Args:
        session: The database session.

    Returns:
        How many organisations were written.
    """
    orgs = session.scalars(select(Organisation).order_by(Organisation.name))
    data = [_serialize_org(session, org) for org in orgs]

    average, n_rated = compute_average_index(data)
    if average is not None:
        print(
            f"Average sovereignty index: {average}) over {n_rated} rated organisations"
        )

    path = _export_output_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_with_brotli(data, path)

    overview_path = path.parent / f"{date.today().isoformat()}.json"
    _write_json_with_brotli(_build_overview(data), overview_path)
    return len(data)
