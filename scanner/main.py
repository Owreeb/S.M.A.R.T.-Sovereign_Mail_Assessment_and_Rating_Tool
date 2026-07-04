"""entrypoint: version orgs from wikidata, scan domains, write to db, dump json"""

import asyncio
from pathlib import Path

from src.db import make_engine, make_session, create_all, scanner_run
from src.domainlist_pipline.org_list_pipeline import wikidata_fetch_and_persist
from src.scanner_pipeline.registry import Registry
from src.scanner_pipeline.to_db import to_db
from src.json_dumper.dump import write_dump

DB_NAME = "SMART.db"
WIKIDATA_CONFIG = Path("src") / "domainlist_pipline" / "config.yaml"

# int = only scan that many (testing), None = everything
SAMPLE_LIMIT: int | None = None


def _domain_query(sample_limit: int | None) -> str:
    query = (
        "SELECT * FROM org_domain_history "
        "WHERE is_current = 1 "
        "AND (website_domain IS NOT NULL OR email_domain IS NOT NULL)"
    )
    if sample_limit is not None:
        query += f" LIMIT {int(sample_limit)}"
    return query


def main(db_path: str | Path | None = None, sample_limit: int | None = SAMPLE_LIMIT) -> None:
    base_dir = Path(__file__).resolve().parent
    if db_path is None:
        db_path = base_dir / "database" / DB_NAME
    db_path = Path(db_path)

    engine = make_engine(db_path)
    create_all(engine)
    Session = make_session(engine)

    with Session() as session:
        with scanner_run(session) as run:
            print("Run ID:", run.id)

            print("Step 0: Versioning the organisation/domain state from Wikidata")
            wikidata_fetch_and_persist(session, run, base_dir / WIKIDATA_CONFIG)
            session.commit()

            scope = "FULL" if sample_limit is None else f"sample of {sample_limit}"
            print(f"Step 1: Scanning domains ({scope})")
            registry = Registry.create_and_run(database=db_path, query=_domain_query(sample_limit))

            print("Step 2: Writing scan results to the database")
            to_db(session, run, registry)

            print("Step 3: Dumping the database to JSON")
            count = write_dump(session)
            print(f"Dumped {count} organisations to JSON")

    print("Finished!")


if __name__ == "__main__":
    main()
