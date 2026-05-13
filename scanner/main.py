from pathlib import Path

from src.domainlist_pipline.bronze_pipeline import save_to_sqlite


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "database" / "raw_data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_sqlite(
        str(db_path),
        "bronze_table",
        str(base_dir / "src" / "domainlist_pipline" / "config.yaml"),
    )

if __name__ == "__main__":
    main()
