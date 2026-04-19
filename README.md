# S.M.A.R.T.

**Sovereign Mail Assessment and Rating Tool**

S.M.A.R.T. analysiert die E-Mail-Infrastruktur öffentlicher Institutionen in Deutschland und bewertet, ob diese souverän betrieben wird oder auf externe Anbieter wie Microsoft 365 angewiesen ist. Die Ergebnisse werden in einer interaktiven Kartenansicht dargestellt.

Entwickelt als Studierendenprojekt an der Hochschule Karlsruhe im Auftrag der [audriga GmbH](https://www.audriga.com), Karlsruhe.

---

## Projektstruktur

```
S.M.A.R.T./
├── scanner/      # Datenpipeline -- sammelt und analysiert Institutionsdaten
├── frontend/     # React SPA -- interaktive Darstellung der Ergebnisse
└── Dokumentation/
```

## Komponenten

### Scanner

Fragt OpenStreetMap-Daten zu deutschen Institutionen (Rathäuser, Gerichte, u.a.) über die Overpass API ab und speichert sie in einer lokalen SQLite-Datenbank. Analysiert anschliessend DNS-Einträge (MX, SPF, IMAP, Webmail) und berechnet einen Souveränitäts-Score je Institution.

Die Pipeline ist nach dem Medallion-Muster aufgebaut (Bronze / Silver / Gold). Die Bronze-Stufe (Rohdatenerfassung) ist implementiert, Silver und Gold folgen.

Siehe [Scanner-Dokumentation](Dokumentation/02_Scanner.md) für Details.

### Frontend

Single Page Application auf Basis von React und TypeScript. Stellt die Scan-Ergebnisse auf einer interaktiven Karte dar, mit Filterung nach Institutionstyp und Detailansicht je Einrichtung.

Aktuell im Aufbau. Siehe [Frontend-Dokumentation](Dokumentation/03_Frontend.md) für Details.

## Schnellstart

### Frontend

Voraussetzung: Node.js 22+

```bash
cd frontend
npm install
npm run dev
```

Die App läuft dann unter `http://localhost:5173`.

### Scanner

Setup-Anleitung folgt nach Abschluss der Technologieentscheidung für den Scanner.

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [Projektübersicht](Dokumentation/00_Uebersicht.md) | Ziel, Scope, fachlicher Kontext |
| [Systemarchitektur](Dokumentation/01_Architektur.md) | Komponenten, Datenfluss, Technologiestack |
| [Scanner](Dokumentation/02_Scanner.md) | Pipeline-Aufbau, Datenbankschema, Logik |
| [Frontend](Dokumentation/03_Frontend.md) | Tech-Stack, geplante Features, CI |
| [Entwicklungsumgebung](Dokumentation/04_Entwicklungsumgebung.md) | Lokales Setup Schritt für Schritt |

## Offene Punkte

- Technologiewahl für den Scanner (Kandidaten: TypeScript/Node.js, Java, Python)
- Implementierung der Silver Pipeline (DNS-Analyse, Score-Berechnung)
- Implementierung der Gold Pipeline und API-Schicht
- Frontend-Anbindung an die Daten

## Lizenz

Noch nicht festgelegt.
