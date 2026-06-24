from pathlib import Path
import yaml

from ..db.models import VendorCategory, MailSystemRole, VendorCountryRating


SIGNATURE_DIR = Path(__file__).resolve().parent / "signatures"

REQUIRED_FIELDS = [
    "role",
    "software",
    "vendor",
    "vendor_country",
    "vendor_category",
    "vendor_country_rating",
    "open_source_rating",
    "vendor_category_rating",
]


class ValidationRunner:
    def __init__(self):
        self.errors = []
        self.corrected = []

    def add_error(self, file, software, msg):
        self.errors.append({
            "file": file,
            "software": software,
            "error": msg
        })

    def add_corrected(self, software):
        self.corrected.append(software)

    def ensure_fields(self, record):
        for f in REQUIRED_FIELDS:
            if f not in record:
                record[f] = None
        return record

    def normalize(self, record, file):
        record = self.ensure_fields(record)
        software = record.get("software")

        # -------------------------
        # Vendor Category
        # -------------------------
        vc = record.get("vendor_category")
        if vc:
            try:
                expected = VendorCategory(vc)
                if record.get("vendor_category_rating") != expected.rating:
                    record["vendor_category_rating"] = expected.rating
                    self.add_corrected(software)
            except ValueError:
                self.add_error(file, software, f"Unknown vendor_category: {vc}")

        # -------------------------
        # Country Rating
        # -------------------------
        country = record.get("vendor_country")
        if country:
            try:
                expected = VendorCountryRating.from_country_code(country)
                if record.get("vendor_country_rating") != expected:
                    record["vendor_country_rating"] = expected
                    self.add_corrected(software)
            except Exception as e:
                self.add_error(file, software, str(e))

        # -------------------------
        # Role (STRICT)
        # -------------------------
        role = record.get("role")
        if not role:
            self.add_error(file, software, "Missing role")
        else:
            try:
                MailSystemRole(role)
            except ValueError:
                # HARD ERROR (optional: skip instead of raise)
                self.add_error(file, software, f"Invalid MailSystemRole: {role}")

        return record


def load_files():
    for f in SIGNATURE_DIR.glob("*.yaml"):
        with open(f, "r", encoding="utf-8") as file:
            yield f.name, yaml.safe_load(file)

def save_files(runner):
    for f in SIGNATURE_DIR.glob("*.yaml"):
        with open(f, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not data:
            continue

        updated = []
        for entry in data:
            entry = runner.normalize(entry, f.name)
            updated.append(entry)

        with open(f, "w", encoding="utf-8") as file:
            yaml.safe_dump(updated, file, sort_keys=False, allow_unicode=True)



def run():
    runner = ValidationRunner()

    for filename, data in load_files():
        if not data:
            continue

        for entry in data:
            runner.normalize(entry, filename)

    # -------------------------
    # FINAL REPORT
    # -------------------------
    print("\n=== CORRECTED ===")
    for c in runner.corrected:
        print(c)

    print("\n=== ERRORS ===")
    for e in runner.errors:
        print(f"{e['file']} | {e['software']} | {e['error']}")
    return runner


if __name__ == "__main__":
    run()