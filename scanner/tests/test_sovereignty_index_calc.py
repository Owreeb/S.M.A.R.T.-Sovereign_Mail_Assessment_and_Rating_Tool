from src.json_dumper.sovereignty_index_calc import (
    _weighted_mean,
    _system_score,
    _role_score,
    compute_sovereignty_index,
    compute_average_index,
)


def _ip(country_rating=None, hoster_rating=None):
    """Minimal serialized IP dict as _system_score expects it."""
    return {"country_rating": country_rating, "hoster_rating": hoster_rating}


def _system(value):
    """A system whose five markers are all ``value``"""
    return {
        "ips": [_ip(country_rating=value, hoster_rating=value)],
        "vendor_category_rating": value,
        "vendor_country_rating": value,
        "open_source_rating": value,
        "proxy": None,
    }


class TestWeightedMean:
    def test_empty_list(self):
        assert _weighted_mean([]) == (None, 0)

    def test_all_none_values(self):
        assert _weighted_mean([(None, 10), (None, 15)]) == (None, 0)

    def test_single_value(self):
        assert _weighted_mean([(4.0, 10)]) == (4.0, 1)

    def test_equal_weights_is_plain_average(self):
        assert _weighted_mean([(2.0, 10), (4.0, 10)]) == (3.0, 2)

    def test_unequal_weights(self):
        assert _weighted_mean([(2.0, 15), (4.0, 5)]) == (2.5, 2)

    def test_none_values_are_dropped(self):
        assert _weighted_mean([(None, 10), (4.0, 10)]) == (4.0, 1)


class TestSystemScore:
    def test_empty_system_is_unrated(self):
        assert _system_score({}) == (None, 0)

    def test_single_marker(self):
        assert _system_score({"open_source_rating": 1}) == (1.0, 1)

    def test_all_five_markers(self):
        assert _system_score(_system(3)) == (3.0, 5)

    def test_ip_ratings_are_averaged(self):
        system = {"ips": [_ip(country_rating=2), _ip(country_rating=4)]}
        assert _system_score(system) == (3.0, 1)

    def test_none_ip_ratings_are_ignored(self):
        system = {"ips": [_ip(country_rating=None, hoster_rating=6)]}
        assert _system_score(system) == (6.0, 1)


class TestRoleScore:
    def test_empty_systems(self):
        assert _role_score([]) == (None, 0)

    def test_single_full_system_no_missing_markers(self):
        assert _role_score([_system(3)]) == (3.0, 0)

    def test_missing_markers_are_counted(self):
        assert _role_score([{"open_source_rating": 1}]) == (1.0, 4)

    def test_several_systems_are_averaged(self):
        assert _role_score([_system(2), _system(4)]) == (3.0, 0)

    def test_proxy_takes_the_weaker_link(self):
        system = {"open_source_rating": 1}
        proxy = {"open_source_rating": 5}
        system["proxy"] = proxy
        score, _ = _role_score([system])
        assert score == 5.0

    def test_proxy_used_when_system_unrated(self):
        system = {"proxy": {"open_source_rating": 3}}
        score, _ = _role_score([system])
        assert score == 3.0


class TestComputeSovereigntyIndex:
    def test_empty_mapping(self):
        assert compute_sovereignty_index({}) is None

    def test_role_with_no_systems(self):
        assert compute_sovereignty_index({"smtp_in": []}) is None

    def test_single_role(self):
        assert compute_sovereignty_index({"imap_pop3": [_system(5)]}) == 5

    def test_rounds_to_nearest_int(self):
        assert compute_sovereignty_index({"smtp_out": [_system(3)]}) == 3

    def test_data_quality_brake_returns_none(self):
        assert compute_sovereignty_index({"imap_pop3": [{"open_source_rating": 1}]}) is None

    def test_multiple_roles(self):
        result = compute_sovereignty_index(
            {"imap_pop3": [_system(2)], "smtp_in": [_system(4)]}
        )
        assert result == 3


class TestComputeAverageIndex:
    def test_empty_list(self):
        assert compute_average_index([]) == (None, 0)

    def test_all_unrated(self):
        assert compute_average_index([{"sovereignty_index": None}, {}]) == (None, 0)

    def test_plain_average(self):
        orgs = [{"sovereignty_index": 3}, {"sovereignty_index": 4}]
        assert compute_average_index(orgs) == (3.5, 2)

    def test_skips_unrated_orgs(self):
        orgs = [{"sovereignty_index": None}, {"sovereignty_index": 2}]
        assert compute_average_index(orgs) == (2, 1)

    def test_rounds_to_two_decimals(self):
        orgs = [
            {"sovereignty_index": 4},
            {"sovereignty_index": 4},
            {"sovereignty_index": 5},
        ]
        assert compute_average_index(orgs) == (4.33, 3)
