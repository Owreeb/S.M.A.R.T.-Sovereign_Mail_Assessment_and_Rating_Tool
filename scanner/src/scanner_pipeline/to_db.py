"""
Writes the scan results from a Registry into the database.

The Registry holds one result DataFrame per Step. This module combines those
frames, renames the columns so they line up with the ORM, extracts the mail
system ratings from the YAML signatures and then writes everything through the
history helpers so we keep a version history over the runs.

Flow of the linking:

    organisation -> domain (email/website) -> mx_domain -> mail system / ip
                                           -> imap host  -> mail system

The ``Domain`` result already carries ``organisation_id`` (it is read from the
DB), so it is the bridge from an organisation to everything we scan.
"""

from __future__ import annotations

import uuid

import pandas as pd

from src.scanner_pipeline.registry import Registry
from src.scanner_pipeline.step import ASN, IMAP, IP, MX, PTR, SMTP, Domain
from src.signatures_pipeline.matcher import SIGNATURE_FIELDS, match_signature
from src.db.history import (
    Session,
    get_or_create,
    update_fields,
    update_history,
)
from src.db.models import (
    IpAddress,
    MailSystem,
    MailSystemIpHistory,
    MailSystemRole,
    OrgMailSystemHistory,
    ScannerRun,
    VendorCountryRating,
    derive_hoster_rating,
)


def _results(registry: Registry, step: type) -> pd.DataFrame:
    """
    Return the result frame for a step, dropping the rows that errored.

    Args:
        registry: the registry with the scan results.
        step: the Step class used as the key.

    Returns:
        A copy of the frame without the ``error`` column and without rows
        where ``error`` was set. Empty frame if the step has no results.
    """
    df = registry.results.get(step)
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    if "error" in df.columns:
        df = df[df["error"].isna()]
    return df.drop(columns=["error"], errors="ignore")


def _as_uuid(value) -> uuid.UUID:
    """Coerce a hex string (or UUID) coming from the DB into a UUID."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


_PROXY_ROLE = MailSystemRole.PROXY.value


def _build_org_domain(domain_df: pd.DataFrame) -> pd.DataFrame:
    """
    Long form of the org -> domain link.

    Melts ``email_domain`` and ``website_domain`` into a single ``domain``
    column so we can join the scan results (which are keyed by domain) back to
    the organisation.

    Returns:
        DataFrame with columns ``organisation_id`` and ``domain``.
    """
    if domain_df.empty:
        return pd.DataFrame(columns=["organisation_id", "domain"])

    frames = []
    for col in ("email_domain", "website_domain"):
        if col in domain_df.columns:
            frames.append(
                domain_df[["organisation_id", col]].rename(columns={col: "domain"})
            )

    if not frames:
        return pd.DataFrame(columns=["organisation_id", "domain"])

    return (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=["domain"])
        .drop_duplicates()
    )


def _build_detections(registry: Registry) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Match the scan results against the signatures.

    Two linking dimensions come out of this:

    * ``mx_detections`` keyed by ``mx_domain`` (from SMTP banners and from the
      MX hostname itself),
    * ``domain_detections`` keyed by ``domain`` (from IMAP banners / hosts).

    Returns:
        A tuple ``(mx_detections, domain_detections)``. Each frame has the
        ``SIGNATURE_FIELDS`` plus its key column.
    """
    columns = ["mx_domain", *SIGNATURE_FIELDS]
    mx_rows: list[dict] = []

    smtp_df = _results(registry, SMTP)
    for row in smtp_df.itertuples(index=False):
        signature = match_signature("smtp", getattr(row, "smtp_banner", None))
        if signature:
            mx_rows.append({"mx_domain": row.mx_domain, **signature})

    mx_df = _results(registry, MX)
    for mx_domain in mx_df.get("mx_domain", pd.Series(dtype=str)).dropna().unique():
        signature = match_signature("mx", mx_domain)
        if signature:
            mx_rows.append({"mx_domain": mx_domain, **signature})

    domain_columns = ["domain", *SIGNATURE_FIELDS]
    domain_rows: list[dict] = []

    imap_df = _results(registry, IMAP)
    for row in imap_df.itertuples(index=False):
        signature = match_signature(
            "imap",
            getattr(row, "banner", None),
            getattr(row, "imap_host", None),
        )
        if signature:
            domain_rows.append({"domain": row.domain, **signature})

    mx_detections = pd.DataFrame(mx_rows, columns=columns).dropna(
        subset=["software", "role"]
    )
    domain_detections = pd.DataFrame(domain_rows, columns=domain_columns).dropna(
        subset=["software", "role"]
    )
    return mx_detections, domain_detections


def _sync_ip_addresses(
    session: Session, run: ScannerRun, registry: Registry
) -> dict[str, IpAddress]:
    """
    Upsert the scanned IP addresses (IP + PTR + ASN) and derive the country
    rating from the country code.

    Returns:
        A map ``ip_address -> IpAddress`` for the history linking later.
    """
    rename_dict = {
        "ip": "ip_address",
        "ptr": "rdns_hostname",
        "asn": "asn",
        "owner": "asn_org",
        "country": "country_code",
    }

    ip_raw = _results(registry, IP)
    ip_df = (
        ip_raw[["ip"]].drop_duplicates()
        if "ip" in ip_raw.columns
        else pd.DataFrame(columns=["ip"])
    )

    ptr_raw = _results(registry, PTR)
    ptr_df = (
        ptr_raw[["ip", "ptr"]]
        if {"ip", "ptr"} <= set(ptr_raw.columns)
        else pd.DataFrame(columns=["ip", "ptr"])
    )

    asn_cols = ["ip", "asn", "owner", "country"]
    asn_raw = _results(registry, ASN)
    asn_df = (
        asn_raw[asn_cols]
        if set(asn_cols) <= set(asn_raw.columns)
        else pd.DataFrame(columns=asn_cols)
    )

    ip_addresses_df = (
        ip_df.merge(ptr_df, on="ip", how="left")
        .merge(asn_df, on="ip", how="left")
        .rename(columns=rename_dict)
        .dropna(subset=["ip_address"])
        .drop_duplicates(subset=["ip_address"])
    )

    ip_map: dict[str, IpAddress] = {}
    for row in ip_addresses_df.to_dict(orient="records"):
        ip, _ = get_or_create(session, IpAddress, ip_address=row["ip_address"])

        values = {k: v for k, v in row.items() if k != "ip_address"}
        values = {k: (None if pd.isna(v) else v) for k, v in values.items()}

        if values.get("asn") is not None:
            try:
                values["asn"] = int(values["asn"])
            except (TypeError, ValueError):
                values["asn"] = None

        country_code = values.get("country_code")
        if country_code:
            try:
                values["country_rating"] = int(
                    VendorCountryRating.from_country_code(country_code)
                )
            except Exception:
                pass

        hoster_rating = derive_hoster_rating(country_code, values.get("asn_org"))
        if hoster_rating is not None:
            values["asn_rating"] = hoster_rating

        update_fields(ip, values)
        ip_map[row["ip_address"]] = ip

    session.flush()
    return ip_map


def _sync_mail_systems(
    mx_detections: pd.DataFrame,
    domain_detections: pd.DataFrame,
    session: Session,
) -> dict[tuple[str, str], MailSystem]:
    """
    Upsert every detected mail system (unique per software + role).

    Returns:
        A map ``(software, role) -> MailSystem`` for the history linking.
    """
    detections = pd.concat(
        [mx_detections[list(SIGNATURE_FIELDS)], domain_detections[list(SIGNATURE_FIELDS)]],
        ignore_index=True,
    ).drop_duplicates(subset=["software", "role"])

    ms_map: dict[tuple[str, str], MailSystem] = {}
    for row in detections.to_dict(orient="records"):
        software = row["software"]
        role_value = row["role"]
        try:
            role = MailSystemRole(role_value)
        except ValueError:
            # signature has a role that is not in the enum -> skip it
            continue

        mail_system, _ = get_or_create(
            session, MailSystem, software=software, role=role
        )
        values = {
            k: v
            for k, v in row.items()
            if k not in ("software", "role") and not pd.isna(v)
        }
        update_fields(mail_system, values)
        ms_map[(software, role_value)] = mail_system

    session.flush()
    return ms_map


def _sync_org_mail_system_history(
    session: Session,
    run: ScannerRun,
    org_domain: pd.DataFrame,
    mx_df: pd.DataFrame,
    mx_detections: pd.DataFrame,
    domain_detections: pd.DataFrame,
    ms_map: dict[tuple[str, str], MailSystem],
) -> None:
    """
    Link organisations to the mail systems detected for their domains.

    A proxy detected together with a server on the same MX is attached to that
    server via ``proxy_system_id`` (so the scorer's max-rule applies). A proxy
    that is the only thing visible on an org's MX is linked on its own; the
    dumper then treats it as the inbound (smtp_in) path.
    """
    # collected as (organisation_id, mail_system, proxy_system_or_None)
    links: list[tuple] = []

    # org -> domain -> mx_domain -> mail system (SMTP banner / MX hostname)
    if not mx_detections.empty and {"domain", "mx_domain"} <= set(mx_df.columns):
        org_mx = org_domain.merge(mx_df[["domain", "mx_domain"]], on="domain")
        org_mx_det = org_mx.merge(mx_detections, on="mx_domain")

        for _, group in org_mx_det.groupby(["organisation_id", "mx_domain"]):
            servers, proxies = [], []
            for rec in group.to_dict(orient="records"):
                mail_system = ms_map.get((rec["software"], rec["role"]))
                if mail_system is None:
                    continue
                (proxies if rec["role"] == _PROXY_ROLE else servers).append(mail_system)

            org_id = group["organisation_id"].iloc[0]
            proxy = proxies[0] if proxies else None
            if servers:
                for server in servers:
                    links.append((org_id, server, proxy))
            else:
                # only a proxy/frontend is visible -> link it on its own
                for proxy_ms in proxies:
                    links.append((org_id, proxy_ms, None))

    # org -> domain -> imap host -> mail system (no proxy pairing)
    if not domain_detections.empty:
        org_dom_det = org_domain.merge(domain_detections, on="domain")
        for rec in org_dom_det.to_dict(orient="records"):
            mail_system = ms_map.get((rec["software"], rec["role"]))
            if mail_system is not None:
                links.append((rec["organisation_id"], mail_system, None))

    # write, de-duplicated on (organisation, mail_system)
    seen: set[tuple] = set()
    for org_id, mail_system, proxy in links:
        key = (str(org_id), mail_system.id)
        if key in seen:
            continue
        seen.add(key)
        update_history(
            session,
            OrgMailSystemHistory,
            run,
            match={
                "organisation_id": _as_uuid(org_id),
                "mail_system_id": mail_system.id,
            },
            tracked={"proxy_system_id": proxy.id if proxy is not None else None},
        )


def _sync_mail_system_ip_history(
    session: Session,
    run: ScannerRun,
    org_domain: pd.DataFrame,
    mx_df: pd.DataFrame,
    mx_detections: pd.DataFrame,
    ip_df: pd.DataFrame,
    ms_map: dict[tuple[str, str], MailSystem],
    ip_map: dict[str, IpAddress],
) -> None:
    """
    Link each organisation's own MX IPs to its mail systems.

    The link is scoped to (organisation, mail_system) -> ip. Because mail
    systems are shared (deduped by software+role), linking by mail_system alone
    would pool every org's IPs onto one row; carrying organisation_id keeps the
    geography per-org.
    """
    if (
        mx_detections.empty
        or ip_df.empty
        or "ip" not in ip_df.columns
        or org_domain.empty
        or not {"domain", "mx_domain"} <= set(mx_df.columns)
    ):
        return

    # org -> mx_domain -> (mail system, ip)
    org_ms_ip = (
        org_domain.merge(mx_df[["domain", "mx_domain"]], on="domain")
        .merge(mx_detections, on="mx_domain")
        .merge(ip_df[["mx_domain", "ip"]], on="mx_domain")[
            ["organisation_id", "software", "role", "ip"]
        ]
        .dropna()
        .drop_duplicates()
    )

    for row in org_ms_ip.to_dict(orient="records"):
        mail_system = ms_map.get((row["software"], row["role"]))
        ip = ip_map.get(row["ip"])
        if mail_system is None or ip is None:
            continue
        update_history(
            session,
            MailSystemIpHistory,
            run,
            match={
                "organisation_id": _as_uuid(row["organisation_id"]),
                "mail_system_id": mail_system.id,
                "ip_address_id": ip.id,
            },
            tracked={},
        )


def to_db(session: Session, run: ScannerRun, registry: Registry) -> None:
    """
    Persist a whole Registry of scan results into the database.

    Args:
        session: the open DB session.
        run: the current ScannerRun (used for the history versioning).
        registry: the registry holding the result frames.
    """
    domain_df = _results(registry, Domain)
    org_domain = _build_org_domain(domain_df)
    mx_df = _results(registry, MX)
    ip_df = _results(registry, IP)

    mx_detections, domain_detections = _build_detections(registry)

    # entities first (so the link tables can reference their ids)
    ip_map = _sync_ip_addresses(session, run, registry)
    ms_map = _sync_mail_systems(mx_detections, domain_detections, session)

    # history / link tables
    _sync_org_mail_system_history(
        session, run, org_domain, mx_df, mx_detections, domain_detections, ms_map
    )
    _sync_mail_system_ip_history(
        session, run, org_domain, mx_df, mx_detections, ip_df, ms_map, ip_map
    )

    session.commit()
