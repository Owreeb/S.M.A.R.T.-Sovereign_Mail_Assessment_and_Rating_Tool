import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domainlist_pipline"))

from email_scraper import (
    normalize_url,
    extract_emails,
    is_generic,
    pick_email_domain,
)


class TestNormalizeUrl:
    def test_adds_https_if_no_scheme(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_keeps_existing_https(self):
        assert normalize_url("https://example.com") == "https://example.com"

    def test_keeps_existing_http(self):
        assert normalize_url("http://example.com") == "http://example.com"

    def test_trims_whitespace(self):
        assert normalize_url("  example.com  ") == "https://example.com"

    def test_empty_string(self):
        assert normalize_url("") == ""

    def test_whitespace_only(self):
        assert normalize_url("   ") == ""


class TestExtractEmails:
    def test_extracts_mailto_href(self):
        assert extract_emails(["mailto:test@example.com"]) == ["test@example.com"]

    def test_extracts_uppercase_mailto(self):
        assert extract_emails(["MAILTO:test@example.com"]) == ["test@example.com"]

    def test_strips_query_params(self):
        assert extract_emails(["mailto:test@example.com?subject=Hello"]) == ["test@example.com"]

    def test_strips_fragment(self):
        assert extract_emails(["mailto:test@example.com#anchor"]) == ["test@example.com"]

    def test_extracts_plain_email(self):
        assert extract_emails(["test@example.com"]) == ["test@example.com"]

    def test_deduplicates(self):
        assert extract_emails(["mailto:a@b.com", "mailto:a@b.com"]) == ["a@b.com"]

    def test_keeps_distinct_emails(self):
        result = extract_emails(["mailto:a@b.com", "mailto:c@d.com"])
        assert result == ["a@b.com", "c@d.com"]

    def test_skips_none(self):
        assert extract_emails([None]) == []

    def test_skips_empty_string(self):
        assert extract_emails([""]) == []

    def test_empty_list(self):
        assert extract_emails([]) == []

    def test_invalid_email_in_href(self):
        assert extract_emails(["mailto:notanemail"]) == []


class TestIsGeneric:
    def test_noreply_is_generic(self):
        assert is_generic("noreply@example.com") is True

    def test_no_reply_with_dash_is_generic(self):
        assert is_generic("no-reply@example.com") is True

    def test_webmaster_is_generic(self):
        assert is_generic("webmaster@example.com") is True

    def test_postmaster_is_generic(self):
        assert is_generic("postmaster@example.com") is True

    def test_admin_is_generic(self):
        assert is_generic("admin@example.com") is True

    def test_hostmaster_is_generic(self):
        assert is_generic("hostmaster@example.com") is True

    def test_mailer_daemon_is_generic(self):
        assert is_generic("mailer-daemon@example.com") is True

    def test_info_is_not_generic(self):
        assert is_generic("info@example.com") is False

    def test_kontakt_is_not_generic(self):
        assert is_generic("kontakt@example.com") is False

    def test_personal_name_is_not_generic(self):
        assert is_generic("john.doe@example.com") is False

    def test_case_insensitive(self):
        assert is_generic("NoReply@example.com") is True


class TestPickEmailDomain:
    def test_returns_domain_of_first_email(self):
        assert pick_email_domain(["info@example.com"]) == "example.com"

    def test_skips_generic_emails(self):
        assert pick_email_domain(["noreply@example.com", "info@other.com"]) == "other.com"

    def test_returns_none_when_all_generic(self):
        assert pick_email_domain(["noreply@example.com", "webmaster@example.com"]) is None

    def test_returns_none_for_empty_list(self):
        assert pick_email_domain([]) is None

    def test_lowercases_domain(self):
        assert pick_email_domain(["info@EXAMPLE.COM"]) == "example.com"

    def test_keeps_subdomain(self):
        assert pick_email_domain(["info@mail.example.com"]) == "mail.example.com"

    def test_picks_first_non_generic(self):
        emails = ["admin@a.com", "info@b.com", "kontakt@c.com"]
        assert pick_email_domain(emails) == "b.com"
