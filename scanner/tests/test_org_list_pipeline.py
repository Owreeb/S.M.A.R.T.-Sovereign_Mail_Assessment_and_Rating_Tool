from src.domainlist_pipline.org_list_pipeline import extract_website_domain, normalize_email_to_domain, WikidataExtractor


class TestExtractWebsiteDomain:
    def test_strips_https(self):
        assert extract_website_domain("https://example.com") == "example.com"

    def test_strips_http(self):
        assert extract_website_domain("http://example.com") == "example.com"

    def test_strips_www(self):
        assert extract_website_domain("https://www.example.com") == "example.com"

    def test_strips_path(self):
        assert extract_website_domain("https://example.com/about") == "example.com"

    def test_strips_port(self):
        assert extract_website_domain("https://example.com:8080") == "example.com"

    def test_lowercases(self):
        assert extract_website_domain("https://EXAMPLE.COM") == "example.com"

    def test_plain_domain(self):
        assert extract_website_domain("example.com") == "example.com"

    def test_returns_none_for_none(self):
        assert extract_website_domain(None) is None

    def test_returns_none_for_empty_string(self):
        assert extract_website_domain("") is None

    def test_returns_none_for_whitespace(self):
        assert extract_website_domain("   ") is None


class TestNormalizeEmailToDomain:
    def test_returns_none_for_none(self):
        assert normalize_email_to_domain(None) is None

    def test_returns_none_for_empty_string(self):
        assert normalize_email_to_domain("") is None

    def test_returns_none_for_whitespace(self):
        assert normalize_email_to_domain("   ") is None

    def test_returns_none_for_non_string(self):
        assert normalize_email_to_domain(123) is None

    def test_strips_mailto_prefix(self):
        assert normalize_email_to_domain("mailto:info@example.com") == "example.com"

    def test_strips_mailto_prefix_case_insensitive(self):
        assert normalize_email_to_domain("MAILTO:info@example.com") == "example.com"

    def test_strips_query_string(self):
        assert normalize_email_to_domain("mailto:info@example.com?subject=Hi") == "example.com"

    def test_strips_fragment(self):
        assert normalize_email_to_domain("mailto:info@example.com#anchor") == "example.com"

    def test_returns_none_when_no_at_sign(self):
        assert normalize_email_to_domain("not-an-email") is None

    def test_lowercases_domain(self):
        assert normalize_email_to_domain("info@EXAMPLE.COM") == "example.com"

    def test_keeps_subdomain(self):
        assert normalize_email_to_domain("info@mail.example.com") == "mail.example.com"

    def test_plain_email_without_mailto(self):
        assert normalize_email_to_domain("info@example.com") == "example.com"


class TestWikidataExtractorParseRows:
    def _make_row(self, **kwargs):
        return {key: {"value": val} for key, val in kwargs.items()}

    def test_parses_full_row(self):
        rows = [self._make_row(
            item="http://www.wikidata.org/entity/Q1",
            name="Test Org",
            cityLabel="Berlin",
            stateLabel="Berlin",
            countryLabel="Deutschland",
            website="https://example.com",
            email="info@example.com",
            coordinates="Point(13.4 52.5)",
        )]
        result = WikidataExtractor._parse_rows(rows, "university")
        assert len(result) == 1
        assert result[0]["name"] == "Test Org"
        assert result[0]["city"] == "Berlin"
        assert result[0]["category_tag"] == "university"

    def test_handles_missing_optional_fields(self):
        rows = [{"item": {"value": "http://www.wikidata.org/entity/Q2"}, "name": {"value": "Minimal Org"}}]
        result = WikidataExtractor._parse_rows(rows, "hospital")
        assert result[0]["city"] is None
        assert result[0]["website"] is None
        assert result[0]["email"] is None

    def test_empty_rows(self):
        assert WikidataExtractor._parse_rows([], "university") == []

    def test_category_tag_is_set(self):
        rows = [{"item": {"value": "Q1"}, "name": {"value": "Org"}}]
        result = WikidataExtractor._parse_rows(rows, "school")
        assert result[0]["category_tag"] == "school"


class TestWikidataExtractorBuildQuery:
    def _make_extractor(self):
        tag_to_qid = {"university": "Q3918"}
        institution_where = {
            "university": """
WHERE {
    ?item wdt:P31/wdt:P279* wd:{TARGET_QID}.
    ?item wdt:P17 wd:{AREA_QID}.
}
GROUP BY ?item
"""
        }
        return WikidataExtractor(tag_to_qid, institution_where)

    def test_query_contains_target_qid(self):
        extractor = self._make_extractor()
        query = extractor.build_query("university", "Q183")
        assert "Q3918" in query

    def test_query_contains_area_qid(self):
        extractor = self._make_extractor()
        query = extractor.build_query("university", "Q183")
        assert "Q183" in query

    def test_query_contains_prefix(self):
        extractor = self._make_extractor()
        query = extractor.build_query("university", "Q183")
        assert "PREFIX wd:" in query
