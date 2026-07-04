"""
dump the current db state into the frontend json format.

sovereignty_index is computed on the fly while dumping (see
sovereignty_index_calc.py).
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
    current ips behind a mail system for one org. scoped to org + mail system
    because mail systems are shared across orgs.
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
    """turn an IpAddress row into the export json dict"""
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
    """turn a mail system (+ optional proxy) into the json dict"""
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
    """newest finished_at (or started_at) among the given runs, or None"""
    if not run_ids:
        return None
    runs = session.scalars(select(ScannerRun).where(ScannerRun.id.in_(run_ids)))
    timestamps = [run.finished_at or run.started_at for run in runs]
    timestamps = [ts for ts in timestamps if ts is not None]
    if not timestamps:
        return None
    # sqlite timestamps come back naive, but a fresh in-memory run is still
    # tz-aware, so strip tzinfo to keep them comparable
    timestamps = [ts.replace(tzinfo=None) for ts in timestamps]
    return max(timestamps).isoformat()


def _slim_system(system: dict[str, Any]) -> dict[str, Any]:
    """
    slim a serialized mail system: drop the bulky per-ip objects, keep the
    distinct host countries + hosters and everything else.
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
    """turn an org into its export json dict"""
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
        # lone proxy is the inbound path, score it as smtp_in
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

    # score on the full thing, then slim for output
    sovereignty_index = compute_sovereignty_index(mail_systems)
    slim_mail_systems = {
        role: [_slim_system(system) for system in systems]
        for role, systems in mail_systems.items()
    }

    # website domain first, fall back to email domain
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
    """top `limit` names by share across the orgs' `key` lists (providers/hosters)"""
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
    """overview: averaged sovereignty index + top vendors and hosters"""
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
    """write data as json + a brotli-compressed .br copy"""
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(payload, encoding="utf-8")
    compressed = brotli.compress(payload.encode("utf-8"))
    path.with_suffix(path.suffix + ".br").write_bytes(compressed)


def _export_output_path(session: Session) -> Path:
    """export path next to the session's db"""
    db_file = session.get_bind().url.database
    return Path(db_file).resolve().parent / "export" / "organizations.json"


def write_dump(session: Session) -> int:
    """
    dump all orgs into <db folder>/export: organizations.json plus a date-named
    overview file. returns how many orgs were written.
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
