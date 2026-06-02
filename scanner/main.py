from pathlib import Path
from src.db import make_engine, make_session, create_all, scanner_run
from src.domainlist_pipline.org_list_pipeline import save_to_sqlite
from src.domainlist_pipline.email_scraper import run_scraper

DB_NAME = "SMART.db"


def main() -> None:

    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "database" / f"{DB_NAME}"

    engine = make_engine(db_path)
    create_all(engine)
    Session = make_session(engine)

    with Session() as session:
        with scanner_run(session) as run:
            print("Run ID:", run.id)


    print("Finished!")

if __name__ == "__main__":
    main()
