"""
End-to-end entrypoint for the S.M.A.R.T. scanner.

Runs the full chain against the existing organisation database:

    1. scan the current domains (DNS/MX/IP/ASN/PTR/SMTP/IMAP),
    2. write the results into the DB (to_db),
    3. dump the DB into the frontend JSON with the sovereignty index.

The organisation list is expected to already be in the database (filled by the
domainlist pipeline / wikidata fetch). Set SAMPLE_LIMIT to a number to scan
only a slice (useful for testing); set it to None for the full run.
"""

import asyncio
from pathlib import Path

from src.db import make_engine, make_session, create_all, migrate_legacy_schema, scanner_run
from src.scanner_pipeline.registry import Registry
from src.scanner_pipeline.to_db import to_db
from src.json_dumper.dump import write_dump

DB_NAME = "SMART.db"

# How many organisation domains to scan in one run.
# An int scans only that many (good for testing); None scans everything.
SAMPLE_LIMIT: int | None = None


def _domain_query(sample_limit: int | None) -> str:
    """Build the query that selects the domains to scan."""
    query = (
        "SELECT * FROM org_domain_history "
        "WHERE is_current = 1 "
        "AND (website_domain IS NOT NULL OR email_domain IS NOT NULL)"
    )
    if sample_limit is not None:
        query += f" LIMIT {int(sample_limit)}"
    return query


def main(db_path: str | Path | None = None, sample_limit: int | None = SAMPLE_LIMIT) -> None:
    """
    Run the full scan -> to_db -> dump chain.

    Args:
        db_path: Path to the SQLite database. Defaults to ``database/SMART.db``
            next to this file.
        sample_limit: How many domains to scan (None = all).
    """
    base_dir = Path(__file__).resolve().parent
    if db_path is None:
        db_path = base_dir / "database" / DB_NAME
    db_path = Path(db_path)

    engine = make_engine(db_path)
    migrate_legacy_schema(engine)
    create_all(engine)
    Session = make_session(engine)

    with Session() as session:
        with scanner_run(session) as run:
            print("Run ID:", run.id)

            scope = "FULL" if sample_limit is None else f"sample of {sample_limit}"
            print(f"Step 1: Scanning domains ({scope})")
            registry = Registry.from_sqlite(db_path, _domain_query(sample_limit))
            asyncio.run(registry.run_queue())

            print("Step 2: Writing scan results to the database")
            to_db(session, run, registry)

            print("Step 3: Dumping the database to JSON")
            count = write_dump(session)
            print(f"Dumped {count} organisations to JSON")

    print("Finished!")


if __name__ == "__main__":
    main()
