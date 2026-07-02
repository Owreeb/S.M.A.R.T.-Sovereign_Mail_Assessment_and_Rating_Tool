"""
End-to-end tests for ``to_db`` with the IMAP-fed IP/ASN pipeline.

The IP step is keyed by a generic ``domain`` column that now carries MX
hostnames *and* IMAP hosts, so these tests pin down that:

* MX servers still get their IPs linked (via ``mx_domain``),
* IMAP servers now get their IPs linked (via ``imap_host``),
* orgs without any signature match fall back to the ``Unidentified Mail
  Server`` for their MX / IMAP host IPs,
* the IMAP IP link is versioned correctly across runs.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pandas as pd
from sqlalchemy import select

from src.db import (
    IpAddress,
    MailSystem,
    MailSystemIpHistory,
    OrgMailSystemHistory,
    Organisation,
    ScannerRun,
    create_all,
    make_engine,
    make_session,
)
from src.scanner_pipeline.step import ASN, IMAP, IP, MX, PTR, SMTP, Domain
from src.scanner_pipeline.to_db import to_db

ORG_A = uuid.uuid4()
ORG_B = uuid.uuid4()


def _registry(imap_a_ip: str = "2.2.2.2") -> SimpleNamespace:
    """
    A fake Registry for two orgs.

    Org A is detected (IONOS MX gateway + Dovecot IMAP); org B has a resolvable
    mail host but matches no signature. ``imap_a_ip`` is the IP org A's IMAP host
    resolves to, so it can change between runs.
    """
    domain = pd.DataFrame(
        [
            {"organisation_id": ORG_A, "email_domain": "a-org.de", "website_domain": None},
            {"organisation_id": ORG_B, "email_domain": "b-org.de", "website_domain": None},
        ]
    )
    mx = pd.DataFrame(
        [
            {"domain": "a-org.de", "mx_domain": "mx.a-org.ionos.de", "error": None},
            {"domain": "b-org.de", "mx_domain": "mail.b-org.de", "error": None},
        ]
    )
    imap = pd.DataFrame(
        [
            {
                "domain": "a-org.de",
                "imap_host": "imap.a-org.de",
                "port": 993,
                "banner": "* OK Dovecot ready",
                "error": None,
            },
            {
                "domain": "b-org.de",
                "imap_host": "mail.b-org.de",
                "port": 993,
                "banner": "* OK server ready",
                "error": None,
            },
        ]
    )
    ip = pd.DataFrame(
        [
            {"domain": "mx.a-org.ionos.de", "ip": "1.1.1.1", "error": None},
            {"domain": "imap.a-org.de", "ip": imap_a_ip, "error": None},
            {"domain": "a-org.de", "ip": "3.3.3.3", "error": None},
            {"domain": "mail.b-org.de", "ip": "4.4.4.4", "error": None},
            {"domain": "b-org.de", "ip": "5.5.5.5", "error": None},
        ]
    )
    asn = pd.DataFrame(
        [
            {"ip": ip_addr, "asn": 100 + i, "owner": owner, "prefix": None, "country": "DE", "error": None}
            for i, (ip_addr, owner) in enumerate(
                [
                    ("1.1.1.1", "IONOS SE"),
                    (imap_a_ip, "Selfhost"),
                    ("3.3.3.3", "Webhost"),
                    ("4.4.4.4", "Hetzner"),
                    ("5.5.5.5", "Webhost"),
                ]
            )
        ]
    )
    return SimpleNamespace(
        results={
            Domain: domain,
            MX: mx,
            IMAP: imap,
            IP: ip,
            ASN: asn,
            PTR: pd.DataFrame(columns=["ip", "ptr", "error"]),
            SMTP: pd.DataFrame(columns=["mx_domain", "smtp_banner", "port", "error"]),
        }
    )


def _session_with_orgs():
    engine = make_engine(":memory:")
    create_all(engine)
    session = make_session(engine)()
    session.add(Organisation(id=ORG_A, name="Org A"))
    session.add(Organisation(id=ORG_B, name="Org B"))
    session.commit()
    return session


def _run(session) -> ScannerRun:
    run = ScannerRun()
    session.add(run)
    session.commit()
    return run


def _current_ip_links(session) -> set[tuple]:
    """(organisation_id, software, ip_address) for every current IP-history row."""
    rows = session.scalars(
        select(MailSystemIpHistory).where(MailSystemIpHistory.is_current.is_(True))
    )
    return {
        (row.organisation_id, row.mail_system.software, row.ip_address.ip_address)
        for row in rows
    }


class TestToDbLinking:
    def test_mx_and_imap_systems_get_their_ips(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry())

        links = _current_ip_links(session)
        # MX gateway -> its mx_domain IP, IMAP server -> its imap_host IP
        assert (ORG_A, "IONOS Mail Gateway", "1.1.1.1") in links
        assert (ORG_A, "Dovecot", "2.2.2.2") in links

    def test_org_domain_ip_is_not_linked(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry())

        # a-org.de itself (3.3.3.3) is a website IP, not a mail host
        ips = {ip for _, _, ip in _current_ip_links(session)}
        assert "3.3.3.3" not in ips
        assert "5.5.5.5" not in ips

    def test_undetected_org_falls_back_to_imap_host_ip(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry())

        links = _current_ip_links(session)
        assert (ORG_B, "Unidentified Mail Server", "4.4.4.4") in links
        # the fallback never touches the detected org
        assert not any(org == ORG_A and sw == "Unidentified Mail Server" for org, sw, _ in links)

    def test_imap_system_is_linked_to_org(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry())

        systems = session.scalars(
            select(OrgMailSystemHistory).where(
                OrgMailSystemHistory.organisation_id == ORG_A,
                OrgMailSystemHistory.is_current.is_(True),
            )
        )
        software = {row.mail_system.software for row in systems}
        assert {"IONOS Mail Gateway", "Dovecot"} <= software


class TestImapIpHistory:
    """
    The IMAP IP link is versioned like the MX one: each (org, mail_system, ip)
    is an append-only presence marker (match on the ip, ``tracked={}``), so a new
    IMAP IP opens its own current row while the old one stays untouched.
    """

    def _dovecot_rows(self, session):
        dovecot = session.scalars(
            select(MailSystem).where(MailSystem.software == "Dovecot")
        ).one()
        return list(
            session.scalars(
                select(MailSystemIpHistory).where(
                    MailSystemIpHistory.organisation_id == ORG_A,
                    MailSystemIpHistory.mail_system_id == dovecot.id,
                )
            )
        )

    def test_rerun_with_same_ip_is_idempotent(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry(imap_a_ip="2.2.2.2"))
        to_db(session, _run(session), _registry(imap_a_ip="2.2.2.2"))

        rows = self._dovecot_rows(session)
        assert len(rows) == 1
        assert rows[0].is_current is True

    def test_new_imap_ip_opens_a_current_link(self):
        session = _session_with_orgs()
        to_db(session, _run(session), _registry(imap_a_ip="2.2.2.2"))
        to_db(session, _run(session), _registry(imap_a_ip="9.9.9.9"))

        current_ips = {
            row.ip_address.ip_address
            for row in self._dovecot_rows(session)
            if row.is_current
        }
        assert "9.9.9.9" in current_ips
