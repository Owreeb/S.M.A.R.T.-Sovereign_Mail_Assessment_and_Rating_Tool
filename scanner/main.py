from pathlib import Path
from src.db import make_engine, make_session, create_all, scanner_run
from src.domainlist_pipline.org_list_pipeline import wikidata_fetch_and_persist
from src.domainlist_pipline.email_scraper import run_scraper

DB_NAME = "SMART.db"


def main() -> None:

    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "database" / f"{DB_NAME}"
    wikidata_config_path = base_dir / "src" / "domainlist_pipline" / "config.yaml"

    engine = make_engine(db_path)
    create_all(engine)
    Session = make_session(engine)

    with Session() as session:
        with scanner_run(session) as run:
            print("Run ID:", run.id)

            print("Step 1: Fetching organisation list from Wikidata")
            wikidata_fetch_and_persist(session, run, wikidata_config_path)
            session.commit()

            #TODO: Run the MX-Record enricher here before scraping email domains

            print("Step 2: Scraping email domains where Website Domain != Email Domain")
            run_scraper(session, run)
            session.commit()

    print("Finished!")

if __name__ == "__main__":
    main()
