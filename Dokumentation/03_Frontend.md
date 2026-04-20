# Frontend -- Technische Dokumentation

## Überblick

Das Frontend ist eine Single Page Application (SPA) auf Basis von React und TypeScript. Es stellt die vom Scanner gesammelten und ausgewerteten Daten interaktiv dar. Die ersten Komponenten und das Datenmodell sind implementiert; die Anbindung an ein Backend steht noch aus.

## Verzeichnisstruktur

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── eslint.config.js
├── .prettierrc
├── .husky/
│   └── pre-commit             # Pre-Commit Hook (Lint + Format)
└── src/
    ├── main.tsx               # Einstiegspunkt
    ├── App.tsx                # Root-Komponente
    ├── theme.ts               # Mantine-Theme (Farben, Schrift, Radius)
    ├── App.css / index.css
    ├── __tests__/
    │   └── statisticsUtils.test.ts
    ├── assets/
    ├── components/
    │   └── statistics/
    │       ├── StatisticsGrid.tsx          # Statistik-Kennzahlen-Komponente
    │       └── StatisticsGrid.module.scss
    ├── constants/
    ├── data/
    │   ├── 2026-02-01-EXAMPLE.json        # Beispieldaten Februar
    │   └── 2026-03-01-EXAMPLE.json        # Beispieldaten März
    ├── hooks/
    ├── models/
    │   └── statisticsData.ts              # TypeScript-Interfaces
    └── utils/
        └── statisticsUtils.ts             # Hilfsfunktionen Differenzberechnung
```

## Technologiestack

| Technologie | Version | Zweck |
|---|---|---|
| React | 19 | UI-Framework |
| TypeScript | ~6.0 | Typsicherheit |
| Vite | 8 | Build-Tool und Dev-Server |
| Mantine | (aktuell) | Komponentenbibliothek (UI, Layout, Styling) |
| Tabler Icons | (aktuell) | Icon-Bibliothek |
| SCSS Modules | (via Vite) | Komponentenlokales Styling |
| Vitest | 4 | Unit-Testing |
| ESLint | 9 | Statische Codeanalyse |
| Prettier | 3 | Code-Formatierung |
| Husky | 9 | Git-Hooks |
| lint-staged | 16 | Staged-Files vor Commit formatieren/linten |

## Theme

Das Mantine-Theme ist in `src/theme.ts` definiert:

- Primärfarbe: Grün (10-stufige Farbskala, Basis `#51cf66`)
- Schrift: Inter (mit System-Fallbacks)
- Standard-Radius: `md`

## Datenmodell

Definiert in `src/models/statisticsData.ts`. Das ist die Schnittstelle zwischen Scanner-Ergebnis und Frontend-Darstellung.

```
StatisticsData
├── overview
│   ├── orgsScanned        Anzahl gescannter Organisationen
│   ├── domainsScanned     Anzahl analysierter Domains
│   ├── sovereigntyIndex   Durchschnittlicher Souveränitätsindex
│   ├── sovereignSystems   Anteil souveräner Systeme (0-1)
│   └── hyperscalerRatio   Anteil Hyperscaler-Nutzung (0-1)
├── sovereigntyDistribution
│   ├── sovereign          Anteil vollständig souverän (0-1)
│   ├── partially          Anteil teilweise souverän (0-1)
│   └── hyperscaler        Anteil Hyperscaler (0-1)
└── topEmailProviders[]
    ├── name               Name des Anbieters (z.B. "Microsoft 365", "Self-Hosted")
    └── share              Marktanteil (0-1)
```

Beispiel-Ausprägung (aus den Testdaten):

```json
{
  "overview": {
    "orgsScanned": 231,
    "domainsScanned": 389,
    "sovereigntyIndex": 6.1,
    "sovereignSystems": 0.57,
    "hyperscalerRatio": 0.29
  },
  "sovereigntyDistribution": {
    "sovereign": 0.57,
    "partially": 0.14,
    "hyperscaler": 0.29
  },
  "topEmailProviders": [
    { "name": "Self-Hosted", "share": 0.40 },
    { "name": "Microsoft 365", "share": 0.25 },
    { "name": "Open-Xchange", "share": 0.15 },
    { "name": "Google", "share": 0.08 },
    { "name": "T-Systems", "share": 0.07 },
    { "name": "DFN", "share": 0.05 }
  ]
}
```

## Datenstrategie (Entwicklungsphase)

Solange kein Backend existiert, arbeitet das Frontend mit statischen JSON-Dateien unter `src/data/`. Diese sind nach dem Muster `YYYY-MM-DD-EXAMPLE.json` benannt und enthalten jeweils einen vollständigen `StatisticsData`-Datensatz für einen Zeitpunkt. Die Komponenten können so zwei Zeitpunkte vergleichen (aktuell vs. vorherig) und Trends als Pfeile darstellen. Sobald das Backend steht, werden diese Dateien durch API-Calls ersetzt.

## Implementierte Komponenten

### StatisticsGrid

Zeigt fünf Kennzahlen als Karten-Grid an: Organisationen gescannt, Souveränitätsindex, Souveräne Systeme, Hyperscaler-Anteil, Domains analysiert. Jede Karte zeigt die aktuelle Zahl sowie den Unterschied zum Vormonat als farbigen Pfeil (grün = besser, rot = schlechter).

Props: `currentData: StatisticsData`, `previousData?: StatisticsData`

## Geplante Features (aus JourFix-Protokoll)

### Landingpage

Eine Einstiegsseite mit Screenshot, Einleitung und Beschreibung des Tools. Erste Ansicht ohne Karte soll den Nutzer abholen.

### Kartenansicht

Interaktive Karte zur Visualisierung der gescannten Institutionen. Geplante Funktionen:

- Mouseover-Effekte auf Institutionen
- Aggregation / Clustering bei hoher Kartendichte
- Darstellung des Souveränitäts-Scores je Institution

### Filterung

Nutzer sollen die Ansicht nach Institutionstypen filtern können (Ministerien, Schulen, u.a.).

### Detailansicht

Pro Institution: Trennung zwischen Sitz und Server/Hosting-Ort, DNS-Analyseergebnisse, Score-Faktoren, Serveranzahl.

## Code-Qualitätssicherung

### Pre-Commit Hook (Husky + lint-staged)

Vor jedem Commit werden alle staged Dateien automatisch formatiert und gelintet:

- `.ts` / `.tsx`: Prettier (Format) + ESLint (Fix)
- `.css` / `.json`: Prettier (Format)

### CI (GitHub Actions)

Bei Push oder Pull Request auf `main` (nur wenn Dateien unter `frontend/` geändert wurden):

1. Node.js 22 einrichten
2. `npm ci` -- saubere Installation aller Abhängigkeiten
3. `npm run lint` -- ESLint-Prüfung
4. `npm run build` -- TypeScript kompilieren und Vite-Build ausführen

Zusätzlich: SonarCloud-Scan (Projekt: `Owreeb_SMART`, Org: `owreeb`).

## Verfügbare npm-Skripte

| Skript | Befehl | Beschreibung |
|---|---|---|
| `dev` | `vite` | Lokalen Dev-Server starten (Hot Reload) |
| `build` | `tsc -b && vite build` | Produktions-Build erstellen |
| `lint` | `eslint .` | Codeanalyse ausführen |
| `test` | `vitest` | Tests ausführen |
| `preview` | `vite preview` | Build-Vorschau starten |
| `format` | `prettier --write "src/**/*.{ts,tsx,css}"` | Alle Quelldateien formatieren |
