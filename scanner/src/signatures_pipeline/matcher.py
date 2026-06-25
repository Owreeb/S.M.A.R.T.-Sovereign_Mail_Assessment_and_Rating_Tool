"""
Matches scan results (SMTP/IMAP banners, MX hostnames) against the YAML
signatures and returns the mail system metadata, including the partial
sovereignty ratings.

The signature files live in ``signatures/`` and are grouped by the scan step
they belong to (``mx``, ``smtp``, ``imap``). Each entry has a ``regex`` plus the
``MailSystem`` fields the match contributes.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

SIGNATURE_DIR = Path(__file__).resolve().parent / "signatures"

# the fields a matched signature contributes to a MailSystem row
SIGNATURE_FIELDS = (
    "software",
    "role",
    "vendor",
    "vendor_country",
    "vendor_category",
    "vendor_country_rating",
    "open_source_rating",
    "vendor_category_rating",
)


@lru_cache(maxsize=None)
def load_signatures(kind: str) -> tuple[dict[str, Any], ...]:
    """
    Load and compile the signatures for one kind (mx/smtp/imap).

    Args:
        kind: name of the signature file without extension.

    Returns:
        A tuple of signature dicts, each with a compiled ``_pattern``.
    """
    path = SIGNATURE_DIR / f"{kind}.yaml"
    if not path.exists():
        return ()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    signatures = []
    for entry in data:
        if not entry or not entry.get("regex"):
            continue
        signatures.append({**entry, "_pattern": re.compile(entry["regex"])})
    return tuple(signatures)


def match_signature(kind: str, *texts: str | None) -> dict[str, Any] | None:
    """
    Return the first ``kind`` signature whose regex matches any of the texts.

    Args:
        kind: which signature file to use (mx/smtp/imap).
        texts: the strings to test (banner, hostname, ...).

    Returns:
        A dict with only the ``SIGNATURE_FIELDS``, or None if nothing matched.
    """
    candidates = [text for text in texts if text]
    if not candidates:
        return None

    for signature in load_signatures(kind):
        pattern = signature["_pattern"]
        if any(pattern.search(text) for text in candidates):
            return {field: signature.get(field) for field in SIGNATURE_FIELDS}
    return None
