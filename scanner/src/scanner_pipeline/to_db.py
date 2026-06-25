from src.scanner_pipeline.registry import Registry
from src.scanner_pipeline.step import IP, PTR, ASN
from src.domainlist_pipline.org_list_pipeline import _clean
from src.db.history import (Session, ScannerRun, get_or_create, update_fields)
from src.db.models import (IpAddress, MailSystem)

import pandas as pd
import yaml
from pathlib import Path

SIGNATURE_DIR = Path(__file__).resolve().parent.parent / "signatures_pipeline" / "signatures"
print(SIGNATURE_DIR)

def _sync_ip_addresses(session: Session, run: ScannerRun, registry: Registry):

    rename_dict = {
        "ip": "ip_address",
        "ptr": "rdns_hostname",
        "asn": "asn",
        "owner": "asn_org",
        "country": "country_code"
    }

    ip_df = registry.results[IP][["ip"]].drop_duplicates()
    ptr_df = registry.results[PTR][["ip", "ptr"]]
    asn_df = registry.results[ASN][["ip", "asn", "owner", "country"]]

    ip_addresses_df = (
        ip_df
        .merge(ptr_df, on="ip", how="left")
        .merge(asn_df, on="ip", how="left")
        .rename(columns=rename_dict)
        .dropna(subset=["ip_address"])
    )
    for row in ip_addresses_df.to_dict(orient="records"):
        ip, _ = get_or_create(
            session,
            IpAddress,
            ip_address=row["ip_address"],
        )

        update_fields(
            ip,
            {k: v for k, v in row.items() if k != "ip_address"}
        )

def _sync_mailsystems(session: Session, run: ScannerRun, registry: Registry):
    """
    id (CHAR(32)) - auto
    role (VARCHAR(9)) - regex? ptr? MailSystemRole
    software (TEXT) - regext? str
    vendor (TEXT) - regex? str
    vendor_country (TEXT) - config based on vendor 
    vendor_category (TEXT) - config based on vendor
    vendor_country_rating (INTEGER) - config based on vendor
    open_source_rating (INTEGER) - config
    vendor_category_rating (INTEGER) - config
    """
    records = []

    for file in SIGNATURE_DIR.glob("*.yaml"):
        print("Opening file", file)
        with open(file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, list):
            records.extend(data)
        else:
            records.append(data)

    if not records:
        return

    mailsystems_df = (
        pd.DataFrame(records)
        .drop_duplicates(subset=["software"])
        .dropna(subset=["software"])
    )

    for row in mailsystems_df.to_dict(orient="records"):
        mailsystem, _ = get_or_create(
            session,
            MailSystem,
            software=row["software"],
        )

        update_fields(
            mailsystem,
            {k: v for k, v in row.items() if k != "software"},
        )

def _sync_org_domain_history(session: Session, run: ScannerRun, registry: Registry):
    pass

def _sync_org_mail_sytem_history(session: Session, run: ScannerRun, registry: Registry):
    pass

def to_db(session: Session, run: ScannerRun, registry: Registry):

    # ip addresses
    _sync_ip_addresses(session, run, registry)
    # mailsystems
    _sync_mailsystems(session, run, registry)
    # org_domain_history

    # org_mail_system_history

    # commit?