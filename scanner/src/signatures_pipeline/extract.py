import os
import re
import yaml
from pathlib import Path


class Extractor:
    def __init__(self, folder_path="."):
        self.folder_path = folder_path
        self.rules = {}
        self._load_all_yaml_files()

    def _load_all_yaml_files(self):
        """Liest alle YAML-Dateien im Ordner und strukturiert sie nach dem Dateinamen."""
        if not os.path.exists(self.folder_path):
            return

        for file_name in os.listdir(self.folder_path):
            if file_name.endswith((".yaml", ".yml")):
                # Key extrahieren (z.B. "asn" aus "asn.yaml")
                key = os.path.splitext(file_name)[0].lower()
                file_path = os.path.join(self.folder_path, file_name)

                with open(file_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f) or []

                    # Wenn die Einträge ein "regex"-Feld haben, kompilieren wir es direkt vor
                    processed_rules = []
                    for item in content:
                        if isinstance(item, dict) and "regex" in item:
                            item["compiled"] = re.compile(item["regex"], re.IGNORECASE)
                        processed_rules.append(item)

                    self.rules[key] = processed_rules

    def get_rules(self, key):
        """Gibt die Regeln für einen bestimmten Key zurück (z.B. 'asn', 'imap')."""
        return self.rules.get(key.lower(), [])

    def match_text(self, key, text):
        """Durchläuft alle Regeln eines Keys, bis ein Regex-Treffer erzielt wird.

        Gibt das gefundene Regel-Dict zurück oder None, wenn nichts matcht.
        """
        rules = self.get_rules(key)
        search_text = str(text)

        for rule in rules:
            if "compiled" in rule and rule["compiled"].search(search_text):
                return rule  # Gibt das komplette Dict aus der YAML zurück

        return None


CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE_PATH.parent.parent.parent
# print(PROJECT_ROOT)
SIGNATURES_DIR = PROJECT_ROOT / "src" / "signatures_pipeline" / "signatures"
# print(SIGNATURES_DIR)

# Das fertige Objekt zur direkten Verwendung im Projekt
extractor = Extractor(folder_path=SIGNATURES_DIR)

if __name__ == "__main__":
    print(extractor.rules)
    print(extractor.match_text("asn", "COLT - COLT Technology Services Group Limited, GB"))
