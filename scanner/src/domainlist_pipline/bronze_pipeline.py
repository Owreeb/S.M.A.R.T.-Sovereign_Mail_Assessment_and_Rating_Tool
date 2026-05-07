import argparse
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
import requests
from sqlalchemy import create_engine
import yaml

MAX_ATTEMPTS = 3
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
    """Extracts the domain from a website URL, also trimming paths, etc."""
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
    return host.lower() or None

class ConfigLoader:
    """Loads institution and area mappings from a YAML file."""

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load(self) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """
        Loads mappings from YAML.

        Returns:
            Tuple of (institutions_map, areas_map, institution_where).
        """
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
    """Builds and executes Wikidata SPARQL queries."""

    def __init__(self, tag_to_qid: dict[str, str], institution_where: dict[str, str]):
        """
        Initializes the extractor.

        Args:
            tag_to_qid: Map of institution keys to QIDs.
            institution_where: Map of institution keys to WHERE clauses.
        """
        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.headers = {'User-Agent': 'GeoInstitutionBot/1.4', 'Accept': 'application/sparql-results+json'}
        self.tag_to_qid = tag_to_qid
        self.institution_where = institution_where

    def build_query(self, institution_key: str, area_qid: str) -> str:
        """
        Builds a SPARQL query from the base template and a WHERE clause.

        Args:
            institution_key: Config key for the institution.
            area_qid: Wikidata QID for the area.

        Returns:
            Fully assembled SPARQL query string.
        """
        target_qid = self.tag_to_qid[institution_key]

        where_template = self.institution_where[institution_key]

        where_clause = (
            where_template
            .replace("{TARGET_QID}", str(target_qid))
            .replace("{AREA_QID}", str(area_qid))
        )
        return f"{SELECT_TEMPLATE}\n{where_clause}"

    def fetch(self, institution_key: str, area_qid: str) -> list[dict[str, str]]:
        """
        Runs a query and returns normalized result rows.

        Args:
            institution_key: Config key for the institution.
            area_qid: Wikidata QID for the area.

        Returns:
            List of result dictionaries (possibly empty).
        """
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
                status = exc.response.status_code if exc.response else None
                if status not in {502, 503, 504}:
                    print(f"Error: {exc}")
                    return []
                if attempt == MAX_ATTEMPTS:
                    print(
                        f"Server error after {MAX_ATTEMPTS} attempts for {institution_key} in {area_qid}."
                    )
                else:
                    print(
                        f"Server error (attempt {attempt}/{MAX_ATTEMPTS}) for {institution_key} in {area_qid}. Retrying..."
                    )
        return []

    @staticmethod
    def _parse_rows(rows: list[dict], institution_key: str) -> list[dict[str, str]]:
        """
        Normalizes SPARQL result bindings.

        Args:
            rows: Raw SPARQL bindings.
            institution_key: Config key for the institution.

        Returns:
            List of normalized rows.
        """
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


def save_to_sqlite(sqlite_path, table_name, config_path="config.yaml"):
    """
    Fetches data and saves it into SQLite.

    Args:
        sqlite_path: Output SQLite file path.
        table_name: Destination table name.
        config_path: Path to config YAML file.
    """
    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    institutions_map, areas_map, institution_where = ConfigLoader(config_path).load()
    extractor = WikidataExtractor(institutions_map, institution_where)

    all_data = []
    for inst_key in institution_where.keys():
        for area_qid in areas_map.values():
            print(f"Loading {inst_key} in {area_qid}...")
            data = extractor.fetch(inst_key, area_qid)
            all_data.extend(data)

    if all_data:
        df = pd.DataFrame(all_data)
        df = df[
            df["website"].fillna("").str.strip().ne("") | df["email"].fillna("").str.strip().ne("")
        ]
        df["website_domain"] = df["website"].apply(extract_website_domain)
        coords = df["coordinates"].str.extract(r"Point\(([-\d.]+)\s+([-\d.]+)\)")
        df["longitude"] = coords[0]
        df["latitude"] = coords[1]
        df.drop(columns=["coordinates"], inplace=True)
        df.drop_duplicates(subset=['id'], inplace=True)
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"Succesfully saved {len(df)} Entries.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    save_to_sqlite(args.db, args.table, args.config)