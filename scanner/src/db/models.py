"""
The ORM models for the scanner database.

The history tables save when something was valid. They do this with the
valid_from_run and valid_to_run columns (which point to scanner_runs) and an
is_current flag. The other tables (organisations, mail_systems, ip_addresses)
just store the entities once without duplicates.
The primary keys get a new uuid automatically.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    REAL,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from enum import IntEnum


class VendorCountryRating(IntEnum):
    """
    Bewertung des Sitzlandes des Herstellers / Anbieters.

    1 = Deutschland
    2 = EU / EWR / Schweiz
    3 = UK oder Drittland mit Angemessenheitsbeschluss (z.B. Japan, Kanada, etc.)
    5 = USA (CLOUD-Act-relevant)
    6 = Hochrisiko- oder sanktionierte Staaten (z.B. Russland, China)
    """

    GERMANY = 1
    EU_EEA_CH = 2
    ADEQUACY_THIRD_COUNTRY = 3
    USA_CLOUD_ACT = 5
    HIGH_RISK_COUNTRY = 6

    @classmethod
    def from_country_code(cls, code: str) -> "VendorCountryRating":
        code = code.upper()

        if code == "DE":
            return cls.GERMANY

        if code in {"AT", "FR", "IT", "ES", "NL", "BE", "PL", "SE", "FI", "DK", "IE", "PT", "GR", "CZ", "SK", "HU", "RO", "BG", "HR", "SI", "LT", "LV", "EE", "LU", "MT", "CY", "NO", "IS", "LI", "CH"}:
            return cls.EU_EEA_CH

        if code == "US":
            return cls.USA_CLOUD_ACT

        if code in {"RU", "CN", "IR", "KP"}:
            return cls.HIGH_RISK_COUNTRY

        # Default: Drittland mit Angemessenheitsbeschluss (vereinfachte Annahme)
        return cls.ADEQUACY_THIRD_COUNTRY


# US hyperscalers / large US clouds -> CLOUD-Act exposed regardless of the
# country their prefix is announced from.
_HYPERSCALER_KEYWORDS = (
    "GOOGLE", "AMAZON", "AWS", "MICROSOFT", "AZURE", "ORACLE",
    "CLOUDFLARE", "AKAMAI", "FASTLY", "DIGITALOCEAN", "LINODE",
)

# Map the vendor-country scale to the IP-hoster scale (Souveränitätsindex V2,
# 4.2). DE/EU operators default to "private EU operator" (2) because we can not
# tell public from cooperative without owner metadata.
_HOSTER_RATING_BY_COUNTRY = {
    VendorCountryRating.GERMANY: 2,
    VendorCountryRating.EU_EEA_CH: 2,
    VendorCountryRating.ADEQUACY_THIRD_COUNTRY: 4,
    VendorCountryRating.USA_CLOUD_ACT: 5,
    VendorCountryRating.HIGH_RISK_COUNTRY: 6,
}


def derive_hoster_rating(country_code, asn_org) -> int | None:
    """
    Simplified IP-hoster rating (Souveränitätsindex V2, scale 4.2).

    1 = public/cooperative EU operator, 2 = private EU operator,
    4 = neutral international carrier, 5 = US hyperscaler / CLOUD-Act,
    6 = sanctioned.

    Args:
        country_code: the ASN country code.
        asn_org: the ASN owner string.

    Returns:
        The rating, or None if there is nothing to base it on.
    """
    if asn_org and any(k in str(asn_org).upper() for k in _HYPERSCALER_KEYWORDS):
        return 5
    if not country_code:
        return None
    base = VendorCountryRating.from_country_code(str(country_code))
    return _HOSTER_RATING_BY_COUNTRY.get(base, 4)


class VendorCategory(str, enum.Enum):
    COMMUNITY_ORG = "Community / Public Sector / Gemeinwohl"
    EU_SOFTWARE_VENDOR = "EU Software Vendor"
    EU_SUBSIDIARY_FOREIGN_VENDOR = "EU Subsidiary of Foreign Vendor"
    INTERNATIONAL_VENDOR = "International Vendor"
    US_HYPERSCALER = "US Hyperscaler"
    UNKNOWN_OR_SANCTIONED = "Unknown / Sanctioned Vendor"

    @property
    def rating(self) -> int:
        return {
            VendorCategory.COMMUNITY_ORG: 1,
            VendorCategory.EU_SOFTWARE_VENDOR: 2,
            VendorCategory.EU_SUBSIDIARY_FOREIGN_VENDOR: 3,
            VendorCategory.INTERNATIONAL_VENDOR: 4,
            VendorCategory.US_HYPERSCALER: 5,
            VendorCategory.UNKNOWN_OR_SANCTIONED: 6,
        }[self]

class MailSystemRole(enum.Enum):
    """The role a mail system has."""

    SMTP_OUT = "smtp_out"
    SMTP_IN = "smtp_in"
    IMAP_POP3 = "imap_pop3"
    WEBMAILER = "webmailer"
    PROXY = "proxy"


class ScannerRun(Base):
    """One run of the scanner. The history tables point to this."""

    __tablename__ = "scanner_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    scanner_version_git_hash: Mapped[str | None] = mapped_column(Text)

    # the history rows that started in this run (valid_from_run == this run)
    opened_domain_history: Mapped[list[OrgDomainHistory]] = relationship(
        back_populates="valid_from",
        foreign_keys="OrgDomainHistory.valid_from_run",
    )
    opened_mail_system_history: Mapped[list[OrgMailSystemHistory]] = relationship(
        back_populates="valid_from",
        foreign_keys="OrgMailSystemHistory.valid_from_run",
    )
    opened_ip_history: Mapped[list[MailSystemIpHistory]] = relationship(
        back_populates="valid_from",
        foreign_keys="MailSystemIpHistory.valid_from_run",
    )


class Organisation(Base):
    """An organisation we scanned. Saved only once."""

    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    wikidata_url: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    category_tag: Mapped[str | None] = mapped_column(Text)
    longitude: Mapped[float | None] = mapped_column(REAL)
    latitude: Mapped[float | None] = mapped_column(REAL)
    website: Mapped[str | None] = mapped_column(Text)

    domain_history: Mapped[list[OrgDomainHistory]] = relationship(
        back_populates="organisation",
        foreign_keys="OrgDomainHistory.organisation_id",
    )
    mail_system_history: Mapped[list[OrgMailSystemHistory]] = relationship(
        back_populates="organisation",
        foreign_keys="OrgMailSystemHistory.organisation_id",
    )


class MailSystem(Base):
    """A mail software with its role. Each software+role is saved only once."""

    __tablename__ = "mail_systems"
    __table_args__ = (UniqueConstraint("software", "role", name="uq_mail_system_software_role"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role: Mapped[MailSystemRole] = mapped_column(
        SAEnum(MailSystemRole, name="mail_system_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    software: Mapped[str] = mapped_column(Text, nullable=False)
    vendor: Mapped[str | None] = mapped_column(Text)
    vendor_country: Mapped[str | None] = mapped_column(Text)
    vendor_category: Mapped[str | None] = mapped_column(Text)

    # partial scores of the sovereignty index
    vendor_country_rating: Mapped[int | None] = mapped_column(Integer)
    open_source_rating: Mapped[int | None] = mapped_column(Integer)
    vendor_category_rating: Mapped[int | None] = mapped_column(Integer)

    # rows where this is the normal mail system
    mail_system_history: Mapped[list[OrgMailSystemHistory]] = relationship(
        back_populates="mail_system",
        foreign_keys="OrgMailSystemHistory.mail_system_id",
    )
    # rows where this is used as a proxy
    proxied_history: Mapped[list[OrgMailSystemHistory]] = relationship(
        back_populates="proxy_system",
        foreign_keys="OrgMailSystemHistory.proxy_system_id",
    )
    ip_history: Mapped[list[MailSystemIpHistory]] = relationship(
        back_populates="mail_system",
        foreign_keys="MailSystemIpHistory.mail_system_id",
    )


class IpAddress(Base):
    """An IP address with its extra info. Saved only once."""

    __tablename__ = "ip_addresses"
    __table_args__ = (UniqueConstraint("ip_address", name="uq_ip_addresses_ip_address"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ip_address: Mapped[str] = mapped_column(Text, nullable=False)
    rdns_hostname: Mapped[str | None] = mapped_column(Text)
    asn: Mapped[int | None] = mapped_column(Integer)
    asn_org: Mapped[str | None] = mapped_column(Text)
    country_code: Mapped[str | None] = mapped_column(Text)

    # partial scores of the sovereignty index
    country_rating: Mapped[int | None] = mapped_column(Integer)
    asn_rating: Mapped[int | None] = mapped_column(Integer)

    ip_history: Mapped[list[MailSystemIpHistory]] = relationship(
        back_populates="ip_address",
        foreign_keys="MailSystemIpHistory.ip_address_id",
    )


class OrgDomainHistory(Base):
    """
    History of the domains of an organisation over the runs.
    """

    __tablename__ = "org_domain_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    valid_from_run: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scanner_runs.id"), nullable=False, index=True
    )
    valid_to_run: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scanner_runs.id"))
    is_current: Mapped[bool | None] = mapped_column(Boolean, index=True)

    email_domain: Mapped[str | None] = mapped_column(Text)
    website_domain: Mapped[str | None] = mapped_column(Text)

    organisation: Mapped[Organisation] = relationship(
        back_populates="domain_history", foreign_keys=[organisation_id]
    )
    valid_from: Mapped[ScannerRun] = relationship(
        back_populates="opened_domain_history", foreign_keys=[valid_from_run]
    )
    valid_to: Mapped[ScannerRun | None] = relationship(foreign_keys=[valid_to_run])


class OrgMailSystemHistory(Base):
    """History that connects an organisation to a mail system over the runs."""

    __tablename__ = "org_mail_system_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    mail_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mail_systems.id"), nullable=False, index=True
    )
    valid_from_run: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scanner_runs.id"), nullable=False, index=True
    )
    valid_to_run: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scanner_runs.id"))
    proxy_system_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mail_systems.id"))
    is_current: Mapped[bool | None] = mapped_column(Boolean, index=True)

    organisation: Mapped[Organisation] = relationship(
        back_populates="mail_system_history", foreign_keys=[organisation_id]
    )
    mail_system: Mapped[MailSystem] = relationship(
        back_populates="mail_system_history", foreign_keys=[mail_system_id]
    )
    proxy_system: Mapped[MailSystem | None] = relationship(
        back_populates="proxied_history", foreign_keys=[proxy_system_id]
    )
    valid_from: Mapped[ScannerRun] = relationship(
        back_populates="opened_mail_system_history", foreign_keys=[valid_from_run]
    )
    valid_to: Mapped[ScannerRun | None] = relationship(foreign_keys=[valid_to_run])


class MailSystemIpHistory(Base):
    """History that connects a mail system to an IP address over the runs."""

    __tablename__ = "mail_system_ip_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    mail_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mail_systems.id"), nullable=False, index=True
    )
    ip_address_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ip_addresses.id"), nullable=False, index=True
    )
    valid_from_run: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scanner_runs.id"), nullable=False, index=True
    )
    valid_to_run: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scanner_runs.id"))
    is_current: Mapped[bool | None] = mapped_column(Boolean, index=True)

    mail_system: Mapped[MailSystem] = relationship(
        back_populates="ip_history", foreign_keys=[mail_system_id]
    )
    ip_address: Mapped[IpAddress] = relationship(
        back_populates="ip_history", foreign_keys=[ip_address_id]
    )
    valid_from: Mapped[ScannerRun] = relationship(
        back_populates="opened_ip_history", foreign_keys=[valid_from_run]
    )
    valid_to: Mapped[ScannerRun | None] = relationship(foreign_keys=[valid_to_run])
