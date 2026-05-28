from pathlib import Path

from src.domainlist_pipline.org_list_pipeline import save_to_sqlite
from src.domainlist_pipline.email_scraper import run_scraper

TABLE_NAME = "bronze_table"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "database" / "raw_data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    config_path = base_dir / "src" / "domainlist_pipline" / "config.yaml"

    print("Step 1: Fetching organisation list from Wikidata")
    save_to_sqlite(str(db_path), TABLE_NAME, str(config_path))

    print("Step 2: Scraping email domains from websites")
    run_scraper(str(db_path), TABLE_NAME)

    print("Finished!")

if __name__ == "__main__":
    main()
