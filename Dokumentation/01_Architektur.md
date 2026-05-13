# Systemarchitektur

## Überblick

S.M.A.R.T. ist als Zwei-Komponenten-System aufgebaut: ein datensammelnder **Scanner** und ein darstellendes **Frontend** (React/TypeScript). Beide Komponenten sind im selben Repository unter den Unterordnern `scanner/` und `frontend/` organisiert.

```
S.M.A.R.T./
├── scanner/        # Datenpipeline -- sammelt und analysiert Institutionsdaten
├── frontend/       # React SPA
└── Dokumentation/
```

## Datenfluss

```
OpenStreetMap (Overpass API)
        |
        v
  Bronze Pipeline          <-- aktuell implementiert
  (Rohdaten sammeln)
        |
        v
  SQLite Datenbank
  (scanner/database/domainlist.db)
        |
        v
  [Silver Pipeline]        <-- geplant: DNS-Abfragen, Score-Berechnung
        |
        v
  [Gold Pipeline]          <-- geplant: aufbereitete Ergebnisse
        |
        v
  [Backend API]            <-- geplant: REST-Schnittstelle zum Frontend
        |
        v
  React Frontend (SPA)
```

## Datenstrategie Frontend (Entwicklungsphase)

Solange die Silver/Gold-Pipeline und die Backend API noch nicht existieren, arbeitet das Frontend mit statischen JSON-Dateien (`src/data/YYYY-MM-DD-EXAMPLE.json`). Diese bilden die spätere API-Antwort nach und enthalten jeweils einen vollständigen `StatisticsData`-Datensatz für einen Zeitpunkt. Dadurch kann das Frontend unabhängig vom Scanner entwickelt und getestet werden. Der Wechsel auf echte API-Calls ist ein späterer Schritt ohne Änderungen am Datenmodell.

## Medallion-Architektur

Der Scanner ist nach dem Medallion-Muster (Bronze / Silver / Gold) konzipiert, das aus dem Data Engineering stammt. Die Idee: Rohdaten werden stufenweise verfeinert.

- **Bronze:** Rohdaten direkt aus der Quelle (OpenStreetMap). Noch keine Analyse, nur strukturiertes Speichern. Bereits implementiert.
- **Silver:** Angereicherte Daten -- DNS-Abfragen (MX, SPF, IMAP-Server, Webmail-Gateway), Identifikation des Mail-Providers, erste Score-Signale. Noch nicht implementiert.
- **Gold:** Fertig aufbereitete, aggregierte Ergebnisse, die direkt vom Frontend konsumiert werden können. Noch nicht implementiert.

## Technologiestack

### Scanner

| Aspekt | Technologie |
|---|---|
| Sprache | **offen** -- zur Diskussion (Kandidaten: TypeScript/Node.js, Java, Python oder andere) |
| Paketverwaltung | abhängig von Sprachwahl |
| OSM-Datenzugriff | Overpass API (HTTP) |
| Datenbank | SQLite (aktueller Prototyp) |
| Einstiegspunkt | CLI (konkrete Umsetzung offen) |

### Frontend

| Aspekt | Technologie |
|---|---|
| Sprache | TypeScript |
| Framework | React 19 |
| Build-Tool | Vite |
| UI-Bibliothek | Mantine |
| Icons | Tabler Icons |
| Styling | SCSS Modules |
| Testing | Vitest |
| Linting | ESLint + Prettier |
| Git Hooks | Husky + lint-staged |

### CI/CD

| Aspekt | Tool |
|---|---|
| Automatisierung | GitHub Actions |
| Code-Qualität | SonarCloud |
| Ticketsystem | Jira |
| Trigger | Push / Pull Request auf `main` (Frontend-Pfade) |

## Komponentenabhängigkeiten

Der Scanner ist vollständig unabhängig vom Frontend. Er wird als separater Prozess ausgeführt und schreibt Ergebnisse in die SQLite-Datenbank. Das Frontend arbeitet in der aktuellen Entwicklungsphase mit statischen Beispieldaten. Eine API-Schicht zwischen Datenbank und Frontend ist geplant; das Datenmodell (`StatisticsData`) ist bereits im Frontend definiert und gibt vor, welche Felder die API liefern muss.
