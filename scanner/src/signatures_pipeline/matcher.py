"""
match scan results (smtp/imap banners, mx hostnames) against the yaml signatures.

signatures live in signatures/ grouped by scan step (mx, smtp, imap); each has a
regex plus the MailSystem fields it contributes.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

SIGNATURE_DIR = Path(__file__).resolve().parent / "signatures"

# fields a matched signature contributes to a MailSystem row
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
    """load + compile the signatures for one kind (mx/smtp/imap)"""
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
    """first `kind` signature matching any of the texts (SIGNATURE_FIELDS only), or None"""
    candidates = [text for text in texts if text]
    if not candidates:
        return None

    for signature in load_signatures(kind):
        pattern = signature["_pattern"]
        if any(pattern.search(text) for text in candidates):
            return {field: signature.get(field) for field in SIGNATURE_FIELDS}
    return None
