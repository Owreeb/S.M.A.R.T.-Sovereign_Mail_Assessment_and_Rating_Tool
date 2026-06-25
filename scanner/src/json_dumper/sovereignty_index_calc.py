"""
Souveränitätsindex V2 calculation.

Calculates the sovereignty grade of an organisation from its serialized
mail_systems dict (the structure the dumper builds), following the
Souveränitätsindex V2 specification in three stages:

1. per-system score: weighted mean of the five markers (ip country,
   ip hoster, vendor category, vendor country, open source),
2. role score: max(system, proxy) a path is only as sovereign as its
   weakest link; several systems of one role are averaged,
3. org grade: 0.6 * weighted role mean + 0.4 * worst role.

Missing markers/roles are dropped and the remaining weights are rescaled. 
If not enough data is available, the org gets no grade.

Scale everywhere: 1 = very sovereign ... 6 = not sovereign.
"""
from typing import Any

# Weights for the five per-system markers
SYS_MARKER_WEIGHTS = {
    "ip_country": 15,
    "ip_hoster": 15,
    "vendor_category": 10,
    "vendor_country": 10, 
    "open_source": 10,  
}

# Role weights for the org aggregation
ROLE_WEIGHTS = {
    "imap_pop3": 0.30,
    "smtp_in": 0.25,
    "smtp_out": 0.25,
    "webmailer": 0.20,
}

# Final grade
ORG_MEAN_SHARE = 0.60
ORG_WORST_SHARE = 0.40

# If on average more than this many of the five per-system markers are not
# determinable, the org gets no grade
MAX_NB_MARKERS_PER_ROLE = 3


def _weighted_mean(pairs: list[tuple]) -> tuple[float | None, int]:
    """
    Weighted mean over pairs

    Args:
        pairs: List of (value, weight) tuples.

    Returns:
        A tuple (mean, number of values that were used).
    """
    pairs = [(value, weight) for value, weight in pairs if value is not None]
    total_weight = sum(weight for _, weight in pairs)
    if total_weight == 0:
        return None, 0
    mean = sum(value * weight for value, weight in pairs) / total_weight
    return mean, len(pairs)


def _system_score(system: dict[str, Any]) -> tuple[float | None, int]:
    """
    Stage 1: per-system score from the five markers.

    Args:
        system: A serialized mail system dict.

    Returns:
        A tuple (score, number of markers).
    """
    ips = system.get("ips") or []
    ip_countries = [ip["country_rating"] for ip in ips if ip["country_rating"] is not None]
    ip_hosters = [ip["hoster_rating"] for ip in ips if ip["hoster_rating"] is not None]
    ip_country = sum(ip_countries) / len(ip_countries) if ip_countries else None
    ip_hoster = sum(ip_hosters) / len(ip_hosters) if ip_hosters else None

    return _weighted_mean([
        (ip_country, SYS_MARKER_WEIGHTS["ip_country"]),
        (ip_hoster, SYS_MARKER_WEIGHTS["ip_hoster"]),
        (system.get("vendor_category_rating"), SYS_MARKER_WEIGHTS["vendor_category"]),
        (system.get("vendor_country_rating"), SYS_MARKER_WEIGHTS["vendor_country"]),
        (system.get("open_source_rating"), SYS_MARKER_WEIGHTS["open_source"]),
    ])


def _role_score(systems: list[dict[str, Any]]) -> tuple[float | None, int]:
    """
    Stage 2: role score with the proxy rule

    Per system the role is max(system, proxy) the proxy sits in front of
    the server, so the path is only as sovereign as its weakest link.
    Several systems of one role are averaged

    Args:
        systems: The serialized systems of one role.

    Returns:
        A tuple (score, number of markers that were not determinable).
    """
    notes = []
    nb_count = 0
    for system in systems:
        score, n_markers = _system_score(system)
        nb_count += len(SYS_MARKER_WEIGHTS) - n_markers
        proxy = system.get("proxy")
        if proxy:
            proxy_score, _ = _system_score(proxy)
            if score is not None and proxy_score is not None:
                score = max(score, proxy_score)
            else:
                score = score if score is not None else proxy_score
        if score is not None:
            notes.append(score)
    if not notes:
        return None, nb_count
    return sum(notes) / len(notes), nb_count


def compute_sovereignty_index(
    mail_systems: dict[str, list[dict[str, Any]]],
) -> int | None:
    """
    Stage 3: the final grade of an organisation.

    Args:
        mail_systems: The mail_systems dict of an org.

    Returns:
        A integer index. Is None if nothing is ratable or the data is too thin
    """
    role_scores: dict[str, float] = {}
    nb_total = 0
    for role in ROLE_WEIGHTS:
        systems = mail_systems.get(role) or []
        if not systems:
            continue
        score, nb_count = _role_score(systems)
        nb_total += nb_count
        if score is not None:
            role_scores[role] = score

    if not role_scores:
        return None

    # data quality brake: too many markers not determinable
    if nb_total > MAX_NB_MARKERS_PER_ROLE * len(role_scores):
        return None

    # weighted mean over the available roles
    weight_sum = sum(ROLE_WEIGHTS[role] for role in role_scores)
    mean = sum(score * ROLE_WEIGHTS[role] for role, score in role_scores.items()) / weight_sum
    worst = max(role_scores.values())
    final = ORG_MEAN_SHARE * mean + ORG_WORST_SHARE * worst

    return int(final + 0.5)


def compute_average_index(
    orgs: list[dict[str, Any]],
) -> tuple[float | None, int]:
    """
    The average sovereignty index over all rated organisations.

    Organisations without an index are skipped.

    Args:
        orgs: The serialized org dicts

    Returns:
        A tuple (average, n_rated). average is the raw mean (e.g.
        4.31), n_rated how many orgs went into it.
    """
    values = [
        org["sovereignty_index"]
        for org in orgs
        if org.get("sovereignty_index") is not None
    ]
    if not values:
        return None, 0
    mean = sum(values) / len(values)
    return round(mean, 2), len(values)
