"""Database package with the ORM models and the engine/session helpers."""

from .base import Base, create_all, make_engine, make_session
from .models import (
    IpAddress,
    MailSystem,
    MailSystemIpHistory,
    MailSystemRole,
    OrgDomainHistory,
    OrgMailSystemHistory,
    Organisation,
    ScannerRun,
)
from .runs import get_git_hash, scanner_run
from .history import get_current, get_or_create, update_fields, update_history

__all__ = [
    "Base",
    "create_all",
    "make_engine",
    "make_session",
    "ScannerRun",
    "Organisation",
    "MailSystem",
    "MailSystemRole",
    "IpAddress",
    "OrgDomainHistory",
    "OrgMailSystemHistory",
    "MailSystemIpHistory",
    "scanner_run",
    "get_git_hash",
    "get_current",
    "get_or_create",
    "update_fields",
    "update_history",
]
