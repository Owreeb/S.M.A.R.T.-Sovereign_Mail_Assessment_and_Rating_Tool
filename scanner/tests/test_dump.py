import sys
import os
import json
from types import SimpleNamespace
import brotli

from src.json_dumper.dump import (
    _serialize_ip,
    _top_shares,
    _build_overview,
    _write_json_with_brotli,
)


class TestSerializeIp:
    def _ip(self):
        return SimpleNamespace(
            ip_address="1.2.3.4",
            rdns_hostname="host.example.com",
            country_code="DE",
            country_rating=2,
            asn_org="Example Hoster",
            asn_rating=3,
        )

    def test_maps_plain_fields(self):
        result = _serialize_ip(self._ip())
        assert result["ip_address"] == "1.2.3.4"
        assert result["rdns_hostname"] == "host.example.com"
        assert result["country_code"] == "DE"
        assert result["country_rating"] == 2

    def test_renames_asn_fields(self):
        result = _serialize_ip(self._ip())
        assert result["hoster"] == "Example Hoster"
        assert result["hoster_rating"] == 3

    def test_only_expected_keys(self):
        assert set(_serialize_ip(self._ip())) == {
            "ip_address",
            "rdns_hostname",
            "country_code",
            "country_rating",
            "hoster",
            "hoster_rating",
        }


class TestTopShares:
    def test_empty_data(self):
        assert _top_shares([], "providers") == []

    def test_none_list_is_treated_as_empty(self):
        assert _top_shares([{"providers": None}], "providers") == []

    def test_missing_key_is_treated_as_empty(self):
        assert _top_shares([{}], "providers") == []

    def test_counts_and_shares(self):
        data = [{"providers": ["A", "B"]}, {"providers": ["A"]}]
        result = _top_shares(data, "providers")
        assert result == [
            {"name": "A", "share": 0.67},
            {"name": "B", "share": 0.33},
        ]

    def test_respects_limit(self):
        data = [{"hosters": ["A", "B", "C"]}]
        assert len(_top_shares(data, "hosters", limit=2)) == 2


class TestBuildOverview:
    def test_empty_data(self):
        result = _build_overview([])
        assert result["overview"] == {
            "orgsScanned": 0,
            "domainsScanned": 0,
            "sovereigntyIndex": None,
        }
        assert result["topMailVendors"] == []
        assert result["topHosters"] == []

    def test_counts_orgs_and_unique_domains(self):
        data = [
            {"email_domain": "a.com", "sovereignty_index": 2, "providers": ["X"], "hosters": ["H"]},
            {"email_domain": "a.com", "sovereignty_index": 4, "providers": ["X"], "hosters": []},
        ]
        result = _build_overview(data)
        assert result["overview"]["orgsScanned"] == 2
        assert result["overview"]["domainsScanned"] == 1
        assert result["overview"]["sovereigntyIndex"] == 3.0

    def test_ignores_orgs_without_domain(self):
        data = [
            {"email_domain": None, "sovereignty_index": 3},
            {"email_domain": "b.com", "sovereignty_index": 3},
        ]
        assert _build_overview(data)["overview"]["domainsScanned"] == 1

    def test_top_lists_are_built(self):
        data = [{"email_domain": "a.com", "sovereignty_index": 1, "providers": ["X"], "hosters": ["H"]}]
        result = _build_overview(data)
        assert result["topMailVendors"] == [{"name": "X", "share": 1.0}]
        assert result["topHosters"] == [{"name": "H", "share": 1.0}]


class TestWriteJson:
    def test_writes_plain_json(self, tmp_path):
        path = tmp_path / "out.json"
        data = {"hello": "world"}
        _write_json_with_brotli(data, path)
        assert json.loads(path.read_text(encoding="utf-8")) == data
