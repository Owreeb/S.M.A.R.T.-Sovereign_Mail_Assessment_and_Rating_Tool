"""
tests for the yaml signatures and the matcher.

focus is the mx-hostname signatures: coverage (curated provider/government hosts
match) and precision (anchored patterns don't fire on look-alikes, e.g. a
bayern.de rule must not match oberbayern.de).
"""

import re

import pytest

from src.signatures_pipeline.matcher import (
    SIGNATURE_FIELDS,
    load_signatures,
    match_signature,
)

# vendor_category -> required vendor_category_rating (mirrors db.models.VendorCategory)
CATEGORY_RATING = {
    "Community / Public Sector / Gemeinwohl": 1,
    "EU Software Vendor": 2,
    "EU Subsidiary of Foreign Vendor": 3,
    "International Vendor": 4,
    "US Hyperscaler": 5,
    "Unknown / Sanctioned Vendor": 6,
}

# vendor_country -> required vendor_country_rating (mirrors VendorCountryRating)
_EU_EEA_CH = {
    "AT", "FR", "IT", "ES", "NL", "BE", "PL", "SE", "FI", "DK", "IE", "PT",
    "GR", "CZ", "SK", "HU", "RO", "BG", "HR", "SI", "LT", "LV", "EE", "LU",
    "MT", "CY", "NO", "IS", "LI", "CH",
}


def _expected_country_rating(code: str) -> int:
    if code == "DE":
        return 1
    if code in _EU_EEA_CH:
        return 2
    if code == "US":
        return 5
    if code in {"RU", "CN", "IR", "KP"}:
        return 6
    return 3


VALID_ROLES = {"smtp_out", "smtp_in", "imap_pop3", "webmailer", "proxy"}

ALL_KINDS = ("mx", "smtp", "imap")


class TestSignatureConsistency:
    """every signature has to be internally consistent and well-formed"""

    @pytest.mark.parametrize("kind", ALL_KINDS)
    def test_category_rating_matches_category(self, kind):
        for sig in load_signatures(kind):
            cat = sig.get("vendor_category")
            if cat is not None:
                assert cat in CATEGORY_RATING, f"{kind}: unknown category {cat!r}"
                assert sig.get("vendor_category_rating") == CATEGORY_RATING[cat], (
                    f"{kind}/{sig.get('software')}: category_rating mismatch for {cat!r}"
                )

    # open-source MTAs are rated maximally sovereign (country 1), deviating from
    # the strict country->rating mapping; deliberate exception
    COUNTRY_RATING_EXCEPTIONS = {"Postfix", "Exim"}

    @pytest.mark.parametrize("kind", ALL_KINDS)
    def test_country_rating_matches_country(self, kind):
        for sig in load_signatures(kind):
            if sig.get("software") in self.COUNTRY_RATING_EXCEPTIONS:
                continue
            code = sig.get("vendor_country")
            if code is not None:
                assert sig.get("vendor_country_rating") == _expected_country_rating(code), (
                    f"{kind}/{sig.get('software')}: country_rating mismatch for {code!r}"
                )

    @pytest.mark.parametrize("kind", ALL_KINDS)
    def test_role_is_valid(self, kind):
        for sig in load_signatures(kind):
            assert sig.get("role") in VALID_ROLES, (
                f"{kind}/{sig.get('software')}: invalid role {sig.get('role')!r}"
            )

    @pytest.mark.parametrize("kind", ALL_KINDS)
    def test_ratings_in_scale(self, kind):
        for sig in load_signatures(kind):
            for field in (
                "vendor_country_rating",
                "vendor_category_rating",
                "open_source_rating",
            ):
                value = sig.get(field)
                if value is not None:
                    assert 1 <= value <= 6, f"{kind}/{sig.get('software')}: {field}={value}"


class TestVendorIdentity:
    """
    mail systems are deduped by (software, role), so two operators sharing a
    software label collapse into one row and lose their identity/rating. every
    software label has to map to a single vendor.
    """

    def test_no_software_label_maps_to_multiple_vendors(self):
        from collections import defaultdict

        by_software: dict[str, set] = defaultdict(set)
        for kind in ALL_KINDS:
            for sig in load_signatures(kind):
                by_software[sig.get("software")].add(sig.get("vendor"))

        collapsing = {
            software: sorted(v for v in vendors if v)
            for software, vendors in by_software.items()
            if len(vendors) > 1
        }
        assert not collapsing, f"software labels shared by multiple vendors: {collapsing}"


class TestMxCoverage:
    """the curated mx hosts resolve to a mail system"""

    # (real mx hostname, expected vendor substring)
    CASES = [
        ("mail.bayern.de", "Bayern"),
        ("mailmx0001.rlp.de", "Rheinland-Pfalz"),
        ("inetmail23.niedersachsen.de", "Niedersachsen"),
        ("mail.justiz-bw.de", "Baden-Württemberg"),
        ("mx-in-30.hessen.de", "Hessen"),
        ("thmail01.thueringen.de", "Thüringen"),
        ("mx1.sachsen-anhalt.de", "Sachsen-Anhalt"),
        ("pmmx-hea-p01.brandenburg.de", "Brandenburg"),
        ("lmtad12.saarland.de", "Saarland"),
        ("mailin.berlin.de", "Berlin"),
        ("mailin.hamburg.de", "Hamburg"),
        ("mx1.landsh.de", "Schleswig-Holstein"),
        ("mx-in.kommunale.it", "Südwestfalen-IT"),
        ("mx.krz.de", "KRZ"),
        ("mta1in.kdo.de", "KDO"),
        ("mailx04.justiz.gv.at", "Österreich"),
        ("mx-78950368.mail.eu.retarus.com", "Retarus"),
        ("any.kundenserver.de", "IONOS"),
        # existing signatures keep working (regression)
        ("mx8.kvnbw.de", "KV Baden-Württemberg"),
        ("foo.mail.protection.outlook.com", "Microsoft"),
    ]

    @pytest.mark.parametrize("host,vendor_sub", CASES)
    def test_host_matches_expected_vendor(self, host, vendor_sub):
        sig = match_signature("mx", host)
        assert sig is not None, f"{host} matched no signature"
        assert vendor_sub.lower() in (sig.get("vendor") or "").lower(), (
            f"{host} -> {sig.get('vendor')!r}, expected to contain {vendor_sub!r}"
        )


class TestMxPrecision:
    """anchored patterns must not fire on look-alike hostnames"""

    NON_MATCHES = [
        "oberbayern.de",            # must not hit the bayern.de rule
        "mail.niederbayern.de",     # ditto
        "verbund.de",               # must not hit the bund.de rule
        "klinikverbund.de",         # real private hospital group, not the federal gov
        "mail.vinzenz-verbund.de",  # ditto
        "example.com",
        "mail.random-firma.de",
    ]

    @pytest.mark.parametrize("host", NON_MATCHES)
    def test_lookalike_does_not_match(self, host):
        assert match_signature("mx", host) is None, f"{host} unexpectedly matched"

    def test_bayern_rule_is_anchored(self):
        assert match_signature("mx", "mail.bayern.de") is not None
        assert match_signature("mx", "oberbayern.de") is None

    def test_bund_rule_matches_federal_but_not_verbund(self):
        # the federal government hosts still match ...
        fed = match_signature("mx", "mx.bund.de")
        assert fed is not None and "Bundesrepublik" in (fed.get("vendor") or "")
        # ... but a private "*verbund.de" must not be mistaken for the federal gov
        assert match_signature("mx", "mail.klinikverbund.de") is None


class TestMatcherContract:
    def test_returns_only_signature_fields(self):
        sig = match_signature("mx", "mail.bayern.de")
        assert set(sig.keys()) == set(SIGNATURE_FIELDS)

    def test_no_text_returns_none(self):
        assert match_signature("mx") is None
        assert match_signature("mx", None) is None

    def test_unknown_kind_returns_none(self):
        assert match_signature("does-not-exist", "anything") is None
