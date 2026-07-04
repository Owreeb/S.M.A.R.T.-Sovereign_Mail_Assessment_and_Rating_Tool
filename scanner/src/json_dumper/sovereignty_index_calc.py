"""
Souveränitätsindex V2: grade an org from its serialized mail_systems.

three stages: per-system score (weighted mean of five markers), role score
(max of system and its proxy, systems of a role averaged), org grade
(0.6 * weighted role mean + 0.4 * worst role). missing markers/roles drop out
and the rest are rescaled; too little data leaves the org unrated.

unidentified systems (software == FALLBACK_SOFTWARE, only ip/hoster known) are
null components: dropped from scoring instead of graded on ip geography alone,
so an org with nothing but fallbacks stays unrated.

scale: 1 = very sovereign ... 6 = not sovereign.
"""
from typing import Any

# label of the ip-only fallback system (set in scanner_pipeline.to_db); it's
# unidentified so it stays out of the score
FALLBACK_SOFTWARE = "Unidentified Mail Server"

# per-system marker weights
SYS_MARKER_WEIGHTS = {
    "ip_country": 15,
    "ip_hoster": 15,
    "vendor_category": 10,
    "vendor_country": 10, 
    "open_source": 10,  
}

# role weights for the org aggregation
ROLE_WEIGHTS = {
    "imap_pop3": 0.30,
    "smtp_in": 0.25,
    "smtp_out": 0.25,
    "webmailer": 0.20,
}

ORG_MEAN_SHARE = 0.60
ORG_WORST_SHARE = 0.40

# too many unknown markers per role and we don't rate the org
MAX_NB_MARKERS_PER_ROLE = 3


def _weighted_mean(pairs: list[tuple]) -> tuple[float | None, int]:
    """weighted mean of (value, weight) pairs, skipping None. returns (mean, n_used)"""
    pairs = [(value, weight) for value, weight in pairs if value is not None]
    total_weight = sum(weight for _, weight in pairs)
    if total_weight == 0:
        return None, 0
    mean = sum(value * weight for value, weight in pairs) / total_weight
    return mean, len(pairs)


def _system_score(system: dict[str, Any]) -> tuple[float | None, int]:
    """stage 1: per-system score from the five markers. returns (score, n_markers)"""
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
    stage 2: role score. per system take max(system, proxy) (weakest link),
    then average the systems. returns (score, n_missing_markers).
    """
    notes = []
    nb_count = 0
    for system in systems:
        # unidentified software, skip it entirely so it neither scores nor
        # counts as missing markers
        if system.get("software") == FALLBACK_SOFTWARE:
            continue
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
    """stage 3: final org grade, or None if nothing's ratable or data's too thin"""
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

    # too much missing, bail
    if nb_total > MAX_NB_MARKERS_PER_ROLE * len(role_scores):
        return None

    weight_sum = sum(ROLE_WEIGHTS[role] for role in role_scores)
    mean = sum(score * ROLE_WEIGHTS[role] for role, score in role_scores.items()) / weight_sum
    worst = max(role_scores.values())
    final = ORG_MEAN_SHARE * mean + ORG_WORST_SHARE * worst

    return int(final + 0.5)


def compute_average_index(
    orgs: list[dict[str, Any]],
) -> tuple[float | None, int]:
    """average sovereignty index over rated orgs. returns (average, n_rated)"""
    values = [
        org["sovereignty_index"]
        for org in orgs
        if org.get("sovereignty_index") is not None
    ]
    if not values:
        return None, 0
    mean = sum(values) / len(values)
    return round(mean, 2), len(values)
