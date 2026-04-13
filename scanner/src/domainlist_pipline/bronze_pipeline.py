from __future__ import annotations
import datetime as dt
import sqlite3
import time
from pathlib import Path
import overpy
from .query_profiles import QUERY_PROFILES

FEDERAL_STATES = [
    ("Baden-Wuerttemberg", "Baden-Wuerttemberg|Baden-Wuerttemberg|Baden-Württemberg"),
    ("Bayern", "Bayern"),
    ("Berlin", "Berlin"),
    ("Brandenburg", "Brandenburg"),
    ("Bremen", "Bremen"),
    ("Hamburg", "Hamburg"),
    ("Hessen", "Hessen"),
    ("Mecklenburg-Vorpommern", "Mecklenburg-Vorpommern"),
    ("Niedersachsen", "Niedersachsen"),
    ("Nordrhein-Westfalen", "Nordrhein-Westfalen"),
    ("Rheinland-Pfalz", "Rheinland-Pfalz"),
    ("Saarland", "Saarland"),
    ("Sachsen", "Sachsen"),
    ("Sachsen-Anhalt", "Sachsen-Anhalt"),
    ("Schleswig-Holstein", "Schleswig-Holstein"),
    ("Thueringen", "Thueringen|Thüringen"),
]

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "domainlist.db"

def build_query(selector: str, federal_state_regex: str) -> str:
    """
    Builds an Overpass QL query string based on the provided selector and federal_state regex.

    Args:
        selector (str): The OSM element selector part of the query.
        federal_state_regex (str): A regex pattern to match the name of the federal state in the query.
        
    Returns:
        str: The constructed Overpass QL query.
    """

    return f"""
        [out:json][timeout:180];
        area["ISO3166-1"="DE"][admin_level=2]->.de;
        area["admin_level"="4"]["name"~"{federal_state_regex}"](area.de)->.state;
        (
        {selector}
        );
        nwr._["highway"!~"."]["railway"!~"."]["public_transport"!~"."];
        nwr._[~"^(website|contact:website|contact:email|wikipedia|wikidata)$"~"."];
        nwr._["name"!~"(\\bDr\\.|\\bProf\\.|\\bDipl\\.|\\bIng\\.)",i];
        out center tags;
    """.strip()

def query_overpass(query: str, retries_per_endpoint: int = 3) -> overpy.Result:
    """
    Executes an Overpass QL query with retry logic and server failover.

    Args:
        query (str): The Overpass QL query string to execute.
        retries_per_endpoint (int): How many times to retry each server before switching.

    Returns:
        overpy.Result: The parsed results from the Overpass API.

    Raises:
        RuntimeError: If all configured servers fail to return a result.
        Exception: If any other than RuntimeError occurs.
    """

    retryable = (
        overpy.exception.OverpassTooManyRequests,
        overpy.exception.OverpassGatewayTimeout,
        overpy.exception.OverpassUnknownHTTPStatusCode,
    )
    last_error: Exception | None = None
    for base_url in OVERPASS_URLS:
        api = overpy.Overpass(url=base_url)
        for attempt in range(1, retries_per_endpoint + 1):
            try:
                return api.query(query)
            except retryable as exc:
                last_error = exc
            except Exception as exc:
                last_error = exc
                raise
            if attempt < retries_per_endpoint:
                wait_seconds = min(2**attempt, 8)
                print(f"Warning: {base_url} failed, Retry in {wait_seconds}s")
                time.sleep(wait_seconds)
        print(f"Switching to next Overpass server")
    raise RuntimeError("Couldnt reach any Overpass server.") from last_error

def _result_rows(result: overpy.Result, profile_name: str, federal_state: str, extracted_at: str) -> list[tuple]:
    """
    Parses an Overpass result into a flattened list of tuples for database insertion.

    Args:
        result (overpy.Result): The raw result object from the Overpass API.
        profile_name (str): The name of the search profile used for this query.
        federal_state (str): The federal state the data belongs to.
        extracted_at (str): A timestamp string indicating when the data was fetched.

    Returns:
        list[tuple]: A list of tuples, where each tuple represents a single OSM element and its relevant tags.
    """

    rows: list[tuple] = []
    for osm_type, elements in (("node", result.nodes), ("way", result.ways), ("relation", result.relations)):
        for item in elements:
            tags = getattr(item, "tags", {}) or {}
            name = str(tags.get("name") or "").strip()
            if not name:
                continue

            item_id = int(getattr(item, "id", 0) or 0)
            rows.append(
                (
                    item_id,
                    osm_type,
                    name,
                    federal_state,
                    tags.get("website"),
                    tags.get("contact:website"),
                    tags.get("contact:email"),
                    tags.get("wikipedia"),
                    tags.get("wikidata"),
                    profile_name,
                    extracted_at,
                )
            )
    return rows

def save_result_to_sqlite(
    result: overpy.Result,
    profile_name: str,
    federal_state: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    
    """
    Saves Overpass results to a SQLite database with deduplication.

    It creates the 'osm_names' table if it doesn't exist. Data is inserted 
    using a 'UNIQUE' constraint to prevent duplicate entries.

    Args:
        result (overpy.Result): The parsed OSM data from Overpass.
        profile_name (str): The name of the search profile used.
        federal_state (str): The German federal state the data belongs to.
        db_path (str): File path to the SQLite database. 

    Returns:
        int: The number of new records actually inserted into the database 
            (excludes ignored duplicates).
    """

    resolved_db_path = Path(db_path)
    if not resolved_db_path.is_absolute():
        resolved_db_path = PROJECT_ROOT / resolved_db_path
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    extracted_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = _result_rows(result, profile_name, federal_state, extracted_at)

    with sqlite3.connect(str(resolved_db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS osm_names (
                id INTEGER,
                osm_type TEXT,
                name TEXT NOT NULL,
                federal_state TEXT,
                website TEXT,
                contact_website TEXT,
                contact_email TEXT,
                wikipedia TEXT,
                wikidata TEXT,
                profil TEXT,
                extracted_at DATETIME,
                UNIQUE(id, osm_type, name, profil, federal_state)
            )
            """
        )
        before = conn.total_changes
        conn.executemany(
            """
            INSERT OR IGNORE INTO osm_names
            (
                id,
                osm_type,
                name,
                federal_state,
                website,
                contact_website,
                contact_email,
                wikipedia,
                wikidata,
                profil,
                extracted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return conn.total_changes - before

def run() -> None:
    """
    Orchestrates the full extraction pipeline for all profiles and federal states.

    Summary of the process:
        1. Iterates through profile names.
        2. For each profile, loops through all federal states.
        3. Builds and executes an Overpass QL query.
        4. Saves results to SQLite with deduplication.

    Returns:
        None
    """

    for profile_name in QUERY_PROFILES:
        selector = QUERY_PROFILES[profile_name]
        total_inserted = 0
        for federal_state, federal_state_regex in FEDERAL_STATES:
            print(f"Searching for '{profile_name}' in {federal_state}")
            query = build_query(selector, federal_state_regex)
            result = query_overpass(query)

            inserted_count = save_result_to_sqlite(result, profile_name, federal_state)
            print(f"Items inserted: {inserted_count}")
            total_inserted += inserted_count

        print(f"Total items inserted: {total_inserted}")