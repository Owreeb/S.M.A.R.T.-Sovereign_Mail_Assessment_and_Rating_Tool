# S.M.A.R.T.

**Sovereign Mail Assessment and Rating Tool**

S.M.A.R.T. analysiert die E-Mail-Infrastruktur öffentlicher Organisationen im
DACH-Raum (Deutschland, Österreich, Schweiz) und bewertet, ob diese souverän
betrieben wird oder auf externe Anbieter wie Microsoft 365 oder Google Workspace
angewiesen ist. Jede Organisation erhält eine Souveränitätsnote von **1 (sehr
souverän) bis 6 (nicht souverän)**. Die Ergebnisse werden in einer interaktiven
Web-Oberfläche (Karte, Statistik-Dashboard, Tabelle) dargestellt.

Entwickelt als Studierendenprojekt an der Hochschule Karlsruhe im Auftrag der
[audriga GmbH](https://www.audriga.com), Karlsruhe.

---

## Projektstruktur

```
S.M.A.R.T./
├── scanner/      # Python-Datenpipeline -- ermittelt & bewertet die Mail-Infrastruktur
├── frontend/     # React SPA -- interaktive Darstellung der Ergebnisse
└── docs/         # vollständige Doku (Scanner & Frontend, technisch & Benutzer, DE/EN)
```

## Komponenten

### Scanner (`scanner/`)

Python-Pipeline (Python 3.12+, [uv](https://docs.astral.sh/uv/)). Baut aus
**Wikidata** eine Liste von Organisationen (Universitäten, Krankenhäuser, Schulen,
Gerichte, Städte) für DE/AT/CH auf, löst je Domain die **MX-/IP-/ASN-/PTR-/SMTP-/
IMAP**-Einträge auf, erkennt Mailprodukte und Hersteller per **Regex-Signaturen**,
speichert alles in einem versionierten **SQLite**-Schema (Historie je Scan-Lauf),
berechnet den **Souveränitätsindex V2** und exportiert das Ergebnis als JSON.

→ [Technische Doku](docs/scanner/technical.de.md) · [Benutzerhandbuch](docs/scanner/user.de.md)

### Frontend (`frontend/`)

Single Page Application auf Basis von **React 19 + Vite + TypeScript** (Mantine,
Leaflet, i18next). Stellt die Scan-Ergebnisse auf einer interaktiven Karte, in
einem Statistik-Dashboard und in einer filterbaren Tabelle dar — zweisprachig
(DE/EN). Rein statischer Build (`npm run build` → `dist/`) — auf einem beliebigen
Webserver hostbar; alle Daten werden zur Buildzeit gebündelt.

→ [Technische Doku](docs/frontend/technical.de.md) · [Benutzerhandbuch](docs/frontend/user.de.md)

## Schnellstart

### Scanner

Voraussetzung: Python 3.12+ und [uv](https://docs.astral.sh/uv/).

```bash
cd scanner
uv sync
uv run main.py
```

Der Export landet in `scanner/database/export/organizations.json` (plus eine
datierte Übersichtsdatei). Details: [Scanner-Benutzerhandbuch](docs/scanner/user.de.md).

### Frontend

Voraussetzung: Node.js 22+.

```bash
cd frontend
npm install
npm run dev
```

Die App läuft dann unter `http://localhost:5173`.

## Dokumentation

Die vollständige Dokumentation liegt im Ordner [`docs/`](docs/README.md) —
technisch und Benutzer, je auf Deutsch und Englisch:

| Komponente | Technisch | Benutzer |
|---|---|---|
| Scanner | [technical.de.md](docs/scanner/technical.de.md) / [.en](docs/scanner/technical.en.md) | [user.de.md](docs/scanner/user.de.md) / [.en](docs/scanner/user.en.md) |
| Frontend | [technical.de.md](docs/frontend/technical.de.md) / [.en](docs/frontend/technical.en.md) | [user.de.md](docs/frontend/user.de.md) / [.en](docs/frontend/user.en.md) |

Weitere Referenzen:

- [Souveränitätsindex V2 – Spezifikation](Souveränitätsindex_V2_Spezifikation.md) — die Bewertungsmethodik
- [DEVELOPMENT.md](DEVELOPMENT.md) — Branching, PR-Regeln, Coding Standards

## Lizenz

[MIT](LICENSE)
