import argparse
import json
import sqlite3
from pathlib import Path


def _row_key(row):
	return row["uuid"]


def dump_domain_data(db_path):
	query = """
		SELECT
			dl.uuid,
			dl.name,
			dl.website_domain,
			dl.category_tag,
			dl.latitude,
			dl.longitude,
			dl.timestamp,
			mx.provider AS provider,
			sr.software_name AS smtp_software
		FROM bronze_table AS dl
		LEFT JOIN domain_list_mx_records AS dlmx
			ON dlmx.domain_list_uuid = dl.uuid
		LEFT JOIN mx_records AS mx
			ON mx.uuid = dlmx.mx_record_uuid
		LEFT JOIN domain_list_smtp_records AS dlsr
			ON dlsr.domain_list_uuid = dl.uuid
		LEFT JOIN smtp_records AS sr
			ON sr.uuid = dlsr.smtp_record_uuid
		WHERE mx.uuid IS NOT NULL OR sr.uuid IS NOT NULL
		ORDER BY dl.uuid
	"""

	results = {}
	with sqlite3.connect(db_path) as conn:
		conn.row_factory = sqlite3.Row
		for row in conn.execute(query):
			key = _row_key(row)
			if key not in results:
				results[key] = {
					"org": row["name"],
					"domain": row["website_domain"],
					"category": row["category_tag"],
					"lat": row["latitude"],
					"long": row["longitude"],
					"provider": [],
					"smtp_software": [],
					"last_checked": row["timestamp"],
				}

			provider = row["provider"]
			if provider and provider not in results[key]["provider"]:
				results[key]["provider"].append(provider)

			smtp_software = row["smtp_software"]
			if smtp_software and smtp_software not in results[key]["smtp_software"]:
				results[key]["smtp_software"].append(smtp_software)

	return list(results.values())


def main():
	parser = argparse.ArgumentParser(
		description="Dump domain data to JSON format.")
	parser.add_argument(
		"--db",
		default=str(Path("database") / "raw_data.db"),
		help="Path to the SQLite database (default: database/raw_data.db).",
	)
	parser.add_argument(
		"--output",
		default=str(Path("data") / "domain_dump.json"),
		help=(
			"Write JSON output to a file "
			"(default: data/domain_dump.json)."
		),
	)
	args = parser.parse_args()

	data = dump_domain_data(args.db)
	payload = json.dumps(data, indent=2, ensure_ascii=True)

	output_path = Path(args.output)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
	main()
