import math
from urllib.parse import urlparse

import pandas as pd
import requests
import tldextract
import yaml

from src.db import (
    Organisation,
    OrgDomainHistory,
    get_current,
    get_or_create,
    update_fields,
    update_history,
)

MAX_ATTEMPTS = 3
PREFIX_TEMPLATE = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
SELECT_TEMPLATE = """
SELECT 
    ?item 
    (SAMPLE(?name_label) AS ?name) 
    (SAMPLE(?website_url) AS ?website) 
    (SAMPLE(?email_addr) AS ?email) 
    (SAMPLE(?coords) AS ?coordinates)
    (SAMPLE(?city_label) AS ?cityLabel) 
    (SAMPLE(?state_label) AS ?stateLabel)
    (SAMPLE(?country_label) AS ?countryLabel)
"""
WHERE_TEMPLATE = """
WHERE {
    ?item wdt:P31/wdt:P279* wd:{TARGET_QID}.
    ?item wdt:P17 wd:{AREA_QID}.
    FILTER NOT EXISTS { ?item wdt:P576 ?dissolved. }
    {EXTRA_FILTERS}

    OPTIONAL { ?item wdt:P856 ?website_url. }
    OPTIONAL { ?item wdt:P968 ?email_addr. }
    OPTIONAL { ?item wdt:P625 ?coords. }
    OPTIONAL {
        ?item wdt:P131* ?city.
        ?city wdt:P31/wdt:P279* wd:Q515.
        ?city rdfs:label ?city_label. FILTER(LANG(?city_label) = "de")
    }
    OPTIONAL {
        ?item wdt:P131* ?state.
        ?state wdt:P31 wd:Q1221156.
        ?state rdfs:label ?state_label. FILTER(LANG(?state_label) = "de")
    }
    OPTIONAL {
        ?item wdt:P17 ?country.
        ?country rdfs:label ?country_label. FILTER(LANG(?country_label) = "de")
    }

    ?item rdfs:label ?name_label. FILTER(LANG(?name_label) = "de")
}
GROUP BY ?item
"""


def extract_website_domain(website: str | None) -> str | None:
    """
    registered domain of a website url (strips subdomain/path/port), so
    en.mannheim.de and www.mannheim.de both become mannheim.de and a change
    only makes a new history entry when the real domain changed.
    """
    if not website or not isinstance(website, str):
        return None

    candidate = website.strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    if not host:
        return None

    host = host.split("/")[0].split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    host = host.lower()
    if not host:
        return None

    registered = tldextract.extract(host).top_domain_under_public_suffix
    return registered or host


def normalize_email_to_domain(email: str | None) -> str | None:
    """domain part of a wikidata email (stored as a 'mailto:...' uri), or None"""
    if not email or not isinstance(email, str):
        return None

    value = email.strip()
    if not value:
        return None

    if value.lower().startswith("mailto:"):
        value = value.split(":", 1)[1]

    value = value.split("?", 1)[0].split("#", 1)[0]

    if "@" not in value:
        return None
    _, _, domain = value.partition("@")
    domain = domain.strip().lower()
    return domain or None

class ConfigLoader:
    """loads institution + area mappings from a yaml file"""

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load(self) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """load (institutions_map, areas_map, institution_where) from yaml"""
        with open(self.config_path, "r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle)

        institutions = data["institutions"]
        areas = data["areas"]

        institutions_map = {}
        institution_where = {}
        for key, value in institutions.items():
            institutions_map[str(key)] = str(value["qid"])
            extra_filters = value.get("filters", [])
            extra_filters_block = "\n".join(extra_filters).rstrip()
            institution_where[str(key)] = str(
                WHERE_TEMPLATE.replace("{EXTRA_FILTERS}", extra_filters_block)
            )

        areas_map = {str(k): str(v) for k, v in areas.items()}
        return institutions_map, areas_map, institution_where


class WikidataExtractor:
    """builds and runs wikidata sparql queries"""

    def __init__(self, tag_to_qid: dict[str, str], institution_where: dict[str, str]):
        self.endpoint_url = "https://qlever.dev/api/wikidata"
        self.headers = {'User-Agent': 'SMART-BOT/1.4', 'Accept': 'application/sparql-results+json'}
        self.tag_to_qid = tag_to_qid
        self.institution_where = institution_where

    def build_query(self, institution_key: str, area_qid: str) -> str:
        """assemble the full sparql query for an institution + area"""
        target_qid = self.tag_to_qid[institution_key]

        where_template = self.institution_where[institution_key]

        where_clause = (
            where_template
            .replace("{TARGET_QID}", str(target_qid))
            .replace("{AREA_QID}", str(area_qid))
        )
        return f"{PREFIX_TEMPLATE}\n{SELECT_TEMPLATE}\n{where_clause}"

    def fetch(self, institution_key: str, area_qid: str) -> list[dict[str, str]]:
        """run the query with retries, normalized rows (empty on failure)"""
        query = self.build_query(institution_key, area_qid)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = requests.get(
                    self.endpoint_url,
                    params={'query': query},
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_rows(data.get('results', {}).get('bindings', []), institution_key)
            except requests.exceptions.RequestException as exc:
                if attempt == MAX_ATTEMPTS:
                    print(
                        f"Request failed after {MAX_ATTEMPTS} attempts for {institution_key} in {area_qid}: {exc}"
                    )
                else:
                    print(
                        f"Request failed (attempt {attempt}/{MAX_ATTEMPTS}) for {institution_key} in {area_qid}: {exc}. Retrying..."
                    )
        return []

    @staticmethod
    def _parse_rows(rows: list[dict], institution_key: str) -> list[dict[str, str]]:
        """flatten sparql bindings into plain row dicts"""
        results = []
        for row in rows:
            results.append({
                "id": row.get('item', {}).get('value'),
                "name": row.get('name', {}).get('value'),
                "city": row.get('cityLabel', {}).get('value'),
                "state": row.get('stateLabel', {}).get('value'),
                "country": row.get('countryLabel', {}).get('value'),
                "website": row.get('website', {}).get('value'),
                "email": row.get('email', {}).get('value'),
                "coordinates": row.get('coordinates', {}).get('value'),
                "category_tag": institution_key,
            })
        return results


def _clean(value):
    """NaN -> None so the orm stores NULL instead of nan"""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _persist_record(session, run, record):
    """
    upsert one org (metadata just overwritten) and version its domains in
    org_domain_history.
    """
    org, _ = get_or_create(
        session, Organisation, wikidata_url=_clean(record.get("id"))
    )
    update_fields(org, {
        "name": _clean(record.get("name")),
        "city": _clean(record.get("city")),
        "state": _clean(record.get("state")),
        "country": _clean(record.get("country")),
        "category_tag": _clean(record.get("category_tag")),
        "longitude": _clean(record.get("longitude")),
        "latitude": _clean(record.get("latitude")),
        "website": _clean(record.get("website")),
    })
    session.flush()

    # wikidata email wins, otherwise keep what's there
    wikidata_email = _clean(record.get("email"))
    current = get_current(session, OrgDomainHistory, organisation_id=org.id)
    email_domain = wikidata_email or (current.email_domain if current else None)

    update_history(
        session,
        OrgDomainHistory,
        run,
        match={"organisation_id": org.id},
        tracked={
            "email_domain": email_domain,
            "website_domain": _clean(record.get("website_domain")),
        },
    )


def fetch_records(config_path):
    """fetch + clean the org rows from wikidata, no db writes"""
    institutions_map, areas_map, institution_where = ConfigLoader(config_path).load()
    extractor = WikidataExtractor(institutions_map, institution_where)

    all_data = []
    for inst_key in institution_where.keys():
        for area_qid in areas_map.values():
            print(f"Loading {inst_key} in {area_qid}...")
            data = extractor.fetch(inst_key, area_qid)
            all_data.extend(data)

    if not all_data:
        return []

    df = pd.DataFrame(all_data)

    df.drop_duplicates(subset=['id'], inplace=True)

    df = df[
        df["website"].fillna("").str.strip().ne("") | df["email"].fillna("").str.strip().ne("")
    ]
    df["website_domain"] = df["website"].apply(extract_website_domain)
    df["email"] = df["email"].apply(normalize_email_to_domain)

    coords = df["coordinates"].astype(str).str.extract(
        r"(?i)POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)"
    )
    df["longitude"] = pd.to_numeric(coords[0], errors="coerce")
    df["latitude"] = pd.to_numeric(coords[1], errors="coerce")
    df.drop(columns=["coordinates"], inplace=True)

    return df.to_dict("records")


def wikidata_fetch_and_persist(session, run, wikidata_config_path):
    """fetch the wikidata orgs and save them"""
    records = fetch_records(str(wikidata_config_path))
    for record in records:
        _persist_record(session, run, record)

    print(f"Saved {len(records)} organisations.")


