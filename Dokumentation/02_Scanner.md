# Scanner -- Technische Dokumentation

## Überblick

Der Scanner ist eine Anwendung, die in mehreren Pipelines Daten zu deutschen Institutionen sammelt, anreichert und auswertet. Der Einstieg erfolgt über eine CLI mit Subcommands.

**Hinweis:** Die Implementierungssprache des Scanners ist noch nicht festgelegt. Kandidaten sind TypeScript/Node.js, Java, Python und andere. Die folgende Dokumentation beschreibt Anforderungen und Verhalten sprachunabhängig. Sprachspezifische Setup-Anleitungen folgen nach der Entscheidung.

## Verzeichnisstruktur (Zielstruktur, sprachunabhängig)

```
scanner/
├── [Einstiegspunkt]                   # CLI-Einstieg (Dateiname je nach Sprache)
├── [Projektkonfiguration]             # z.B. package.json, pom.xml, pyproject.toml
├── database/
│   └── domainlist.db                  # SQLite-Datenbank (wird bei erstem Run erzeugt)
└── src/
    └── domainlist_pipeline/
        ├── bronze_pipeline.[ext]      # Bronze-Stufe der Datenpipeline
        └── query_profiles.[ext]       # OSM-Abfrageprofile
```

## CLI-Nutzung

Der Scanner wird als CLI-Anwendung mit Subcommands betrieben:

```
[runner] [einstiegspunkt] <subcommand>
```

Verfügbare Subcommands:

| Subcommand | Beschreibung |
|---|---|
| `run_bronze` | Startet die Bronze Pipeline (OSM-Daten sammeln) |

## Bronze Pipeline

Die Bronze Pipeline ist die erste Stufe der Datenverarbeitung. Sie fragt OpenStreetMap-Daten über die Overpass API ab und speichert die Rohergebnisse in einer SQLite-Datenbank.

### Ablauf

1. Für jedes Query-Profil (z.B. "rathaus", "gericht") wird iteriert.
2. Für jedes Profil wird jedes der 16 Bundesländer abgefragt.
3. Es wird eine Overpass QL-Abfrage gebaut und gegen die API ausgeführt.
4. Ergebnisse werden in die SQLite-Datenbank geschrieben (Duplikate werden ignoriert).

### Overpass-Server (Failover)

Der Scanner nutzt mehrere Overpass-Server mit automatischem Failover und exponentiellem Backoff (max. 8 Sekunden Wartezeit):

- `https://overpass-api.de/api/interpreter`
- `https://lz4.overpass-api.de/api/interpreter`
- `https://overpass.kumi.systems/api/interpreter`

### Filterlogik der Overpass-Abfrage

Die Abfrage schränkt Ergebnisse bewusst ein:

- Ausgeschlossen: Elemente mit `highway`, `railway` oder `public_transport`-Tags (Verkehrsinfrastruktur)
- Pflicht: Mindestens ein Web- oder Kontakt-Tag muss vorhanden sein (`website`, `contact:website`, `contact:email`, `wikipedia`, `wikidata`)
- Ausgeschlossen: Namen mit akademischen Titeln (`Dr.`, `Prof.`, `Dipl.`, `Ing.`) -- filtert Einzelpersonen heraus

### Query-Profile

Definiert in einem dedizierten Modul `query_profiles`:

| Profilname | OSM-Selektor | Bedeutung |
|---|---|---|
| `rathaus` | `nwr["amenity"="townhall"]` | Rathäuser |
| `gericht` | `nwr["amenity"="courthouse"]` | Gerichte |

Neue Profile können durch Ergänzung dieser Zuordnung hinzugefügt werden, ohne weitere Änderungen am Kerncode vornehmen zu müssen.

## Datenbankschema

Datenbank: `scanner/database/domainlist.db` (SQLite)

### Tabelle: `osm_names`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER | OSM-Element-ID |
| `osm_type` | TEXT | Elementtyp: `node`, `way` oder `relation` |
| `name` | TEXT | Name der Institution (Pflichtfeld) |
| `federal_state` | TEXT | Bundesland |
| `website` | TEXT | OSM-Tag `website` |
| `contact_website` | TEXT | OSM-Tag `contact:website` |
| `contact_email` | TEXT | OSM-Tag `contact:email` |
| `wikipedia` | TEXT | OSM-Tag `wikipedia` |
| `wikidata` | TEXT | OSM-Tag `wikidata` |
| `profil` | TEXT | Name des Query-Profils (z.B. "rathaus") |
| `extracted_at` | DATETIME | Zeitstempel der Extraktion |

Eindeutigkeitsbedingung: `(id, osm_type, name, profil, federal_state)` -- verhindert Duplikate bei wiederholten Läufen.

## Logische Komponenten

Unabhängig von der Implementierungssprache muss der Scanner folgende Funktionsblöcke bereitstellen:

**Query Builder:** Nimmt ein Profil und ein Bundesland entgegen, erzeugt daraus eine vollständige Overpass QL-Abfrage als String.

**Overpass Client:** Führt eine Overpass QL-Abfrage gegen einen der konfigurierten Server aus. Implementiert Retry-Logik mit Backoff und Server-Failover. Wirft einen Fehler, wenn alle Server nicht erreichbar sind.

**Result Parser:** Wandelt das Rohergebnis der Overpass API in flache Datensätze um, die direkt in die Datenbank geschrieben werden können. Filtert Elemente ohne Namen heraus.

**Database Writer:** Schreibt die geparsten Datensätze in die SQLite-Datenbank. Erstellt die Tabelle bei Bedarf. Verwendet Upsert-Semantik (kein Fehler bei Duplikaten, einfach überspringen).

**Pipeline Orchestrator:** Verknüpft die obigen Komponenten und iteriert über alle Profile und Bundesländer.

## Geplante Erweiterungen

- **Silver Pipeline:** DNS-Abfragen (MX, SPF, IMAP-Server, Webmail-Gateway) für jede gefundene Domain
- **Gold Pipeline:** Score-Berechnung je Institution und Aufbereitung für das Frontend
- **API-Schicht:** REST-Endpunkte zur Datenabfrage durch das Frontend (Datenformat: siehe `StatisticsData` in [Frontend-Dokumentation](03_Frontend.md))

## Hinweise

- Die Datenbank wird automatisch angelegt -- das Datenbankverzeichnis muss nicht manuell erstellt werden.
- Lange Laufzeiten sind zu erwarten: alle 16 Bundesländer werden pro Profil einzeln abgefragt, Wartezeiten durch Retries kommen hinzu.
