from scrapy.http import HtmlResponse

from src.domainlist_pipline.email_scraper import (
    normalize_url,
    extract_emails,
    is_generic,
    pick_email_domain,
    find_impressum_link,
)


def _make_response(body: str, url: str = "https://example.com") -> HtmlResponse:
    return HtmlResponse(url=url, body=body.encode("utf-8"), encoding="utf-8")


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


class TestFindImpressumLink:
    def test_finds_link_by_visible_text(self):
        response = _make_response('<a href="/impressum">Impressum</a>')
        assert find_impressum_link(response) == "https://example.com/impressum"

    def test_finds_link_by_kontakt_text(self):
        response = _make_response('<a href="/about">Kontakt</a>')
        assert find_impressum_link(response) == "https://example.com/about"

    def test_finds_link_by_href_keyword(self):
        response = _make_response('<a href="/impressum.html">Legal</a>')
        assert find_impressum_link(response) == "https://example.com/impressum.html"

    def test_text_match_is_case_insensitive(self):
        response = _make_response('<a href="/page">IMPRESSUM</a>')
        assert find_impressum_link(response) == "https://example.com/page"

    def test_returns_none_when_no_match(self):
        response = _make_response('<a href="/home">Home</a><a href="/about">About us</a>')
        assert find_impressum_link(response) is None

    def test_returns_none_for_empty_page(self):
        assert find_impressum_link(_make_response("<html></html>")) is None

    def test_ignores_mailto_links(self):
        response = _make_response('<a href="mailto:impressum@example.com">Impressum</a>')
        assert find_impressum_link(response) is None

    def test_ignores_tel_links(self):
        response = _make_response('<a href="tel:+49123">Kontakt</a>')
        assert find_impressum_link(response) is None

    def test_ignores_fragment_links(self):
        response = _make_response('<a href="#impressum">Impressum</a>')
        assert find_impressum_link(response) is None

    def test_ignores_javascript_links(self):
        response = _make_response('<a href="javascript:void(0)">Impressum</a>')
        assert find_impressum_link(response) is None

    def test_picks_first_match_when_multiple(self):
        response = _make_response(
            '<a href="/impressum">Impressum</a><a href="/kontakt">Kontakt</a>'
        )
        assert find_impressum_link(response) == "https://example.com/impressum"

    def test_resolves_relative_url_to_absolute(self):
        response = _make_response(
            '<a href="legal/impressum">Impressum</a>',
            url="https://example.com/de/",
        )
        assert find_impressum_link(response) == "https://example.com/de/legal/impressum"

    def test_keeps_absolute_http_url(self):
        response = _make_response(
            '<a href="http://other.de/impressum">Impressum</a>'
        )
        assert find_impressum_link(response) == "http://other.de/impressum"
