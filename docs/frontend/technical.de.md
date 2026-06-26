# S.M.A.R.T. Frontend — Technische Dokumentation (DE)

Das Frontend ist eine **Vite-+-React-19-+-TypeScript**-Single-Page-Application, die
die Souveränitätsdaten des Scanners visualisiert. Es rendert eine Landingpage, eine
interaktive Karte, ein Statistik-Dashboard, eine filterbare Tabelle und eine Seite
zur Bewertungsmethodik. Es ist eine **statische Site** (alle Daten werden zur
Buildzeit gebündelt), deployt auf **GitHub Pages**.

Nicht-technische Bedienung: [user.de.md](user.de.md). Englische Fassung:
[technical.en.md](technical.en.md).

---

## 1. Technologie-Stack

| Aspekt | Wahl |
|---|---|
| Build-Tool | **Vite 8** (`@vitejs/plugin-react`) |
| UI-Laufzeit | **React 19** + **React Compiler** (Babel-Preset, in `vite.config.ts` aktiviert) |
| Komponenten-Kit | **Mantine 9** (`@mantine/core`, `@mantine/hooks`) — Provider + Theme; das meiste Layout ist eigenes SCSS |
| Karte | **Leaflet 1.9** + **react-leaflet 5** + `leaflet.markercluster` + `leaflet-geosearch` |
| Routing | **react-router-dom 7** (`BrowserRouter`) |
| i18n | **i18next 25** + **react-i18next 16** (Deutsch Default, Englisch Alternative) |
| Icons | `@tabler/icons-react`; Länderflaggen via `flag-icons`-CSS |
| Markdown | `react-markdown` + `remark-gfm` (rendert die Score-Spezifikation) |
| Datumsformat | `dayjs` (Karten-Popups) |
| Styling | **SCSS-Module** (`sass-embedded`), eine `*.module.scss` je Komponente |
| Tests | **Vitest 4** (+ `@vitest/coverage-v8`) |
| Lint/Format | ESLint 9 (Flat Config) + Prettier (mit Import-Sort-Plugin) |
| Git-Hooks | **Husky** + **lint-staged** (pre-commit) |

> Der Memo-Hinweis „nutzt `@mantine/charts`“ ist veraltet — es gibt **keine**
> `@mantine/charts`-Abhängigkeit; alle Balken/Histogramme sind handgebaute `<div>`s
> mit inline `width`/`background`.

### Scripts (`package.json`)

| Script | Befehl | Zweck |
|---|---|---|
| `dev` | `vite` | Dev-Server (http://localhost:5173) |
| `build` | `tsc -b && vite build` | Typecheck, dann Build |
| `lint` | `eslint .` | Linting |
| `test` | `vitest` | Tests ausführen |
| `preview` | `vite preview` | Production-Build vorschauen |
| `format` | `prettier --write "src/**/*.{ts,tsx,css}"` | Formatieren |

---

## 2. Architektur: Bootstrap, Routing, Datenfluss

### Bootstrap — `src/main.tsx`

```
<StrictMode>
  <MantineProvider theme={theme} defaultColorScheme="light">
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <App />
```

Side-Effect-Importe initialisieren die App: `flag-icons`-CSS, Mantine-CSS und
**`./i18n/i18n`** (i18next initialisiert synchron beim Import). Der `basename` des
`BrowserRouter` ist der GitHub-Pages-Basispfad.

### Routing — `src/App.tsx`

`App` ist *nur* eine Routen-Tabelle — **kein Daten-Laden, keine Context-Provider**:

| Pfad | Seite |
|---|---|
| `/` | `LandingPage` |
| `/dashboard` | `Dashboard` |
| `/score-info` | `ScoreInfo` |

### Datenfluss (wichtig)

Die Daten werden **auf Modulebene in `Dashboard.tsx`** geladen, nicht in
`App.tsx`, und es gibt **keinen React-Context** — alles wird per Props übergeben.
Eine einzige `useOrgFilters`-Hook-Instanz (in `Dashboard` erzeugt) wird zwischen
Karte und Tabelle geteilt, damit beide synchron bleiben.

```
src/data/organizations.json  ──statischer Import──┐
src/data/<date>.json (import.meta.glob, eager)     │
                                                   ▼
                              Dashboard.tsx (Modulebene)
   organizations = organizationsData.filter(o => o.sovereignty_index != null)
   currentData / previousData = neueste / zweitneueste datierte Übersichtsdatei
                                                   │
            useOrgFilters(organizations) ─────────┤
                                                   ▼
   <OverviewSection currentData previousData />     (Stat-Cards + Top-Shares)
   <InsightsSection orgs={organizations} />         (clientseitig berechnete Histogramme)
   <MapView orgs filters />                         (Leaflet + Cluster + Popups)
   <OrgTable orgs={filters.filteredOrgs} filters /> (Suche + Pagination)
```

Unbewertete Organisationen (`sovereignty_index == null`) werden **vollständig**
aus dem Dashboard entfernt. Das Frontend lädt zur Laufzeit nichts nach — alles
JSON wird von Vite gebündelt.

### Theme — `src/theme.ts`

Mantine `createTheme`: `primaryColor: 'green'`, Inter-Font, `defaultRadius: 'md'`,
eine eigene 10-stufige Grün-Palette und ein Default, der alle `Paper` weiß macht.

---

## 3. Projektaufbau

```
frontend/src/
├── main.tsx · App.tsx · theme.ts
├── pages/
│   ├── Dashboard.tsx          # Daten-Hub: lädt JSON, verdrahtet Sektionen
│   ├── LandingPage.tsx        # Marketing-Seite (keine Daten)
│   └── ScoreInfo.tsx          # rendert die V2-Spezifikation als Markdown
├── components/
│   ├── landing/   Hero · Navbar · FeaturesSection · SovereigntySection · Footer
│   ├── map/       MapView · ClusteredMarkers · FilterPanel · Legend · SearchControl
│   ├── statistics/ OverviewSection · StatisticsGrid · StatCard · TopShares · InsightsSection
│   ├── table/     OrgTable · FilterChips · tableColumns
│   └── common/    LanguageSwitch
├── models/        organization.ts · statisticsData.ts     # der Scanner-Vertrag
├── utils/         sovereignty · statisticsUtils · mailInsights · categoryUtils · countryUtils · translationUtils
├── hooks/         useOrgFilters.ts
├── constants/     filterFields.ts
├── i18n/          i18n.ts · resources.ts · i18next.d.ts · locales/{de,en}/<ns>.ts
├── data/          organizations.json · <date>.json        # Scanner-Export
└── __tests__/     statisticsUtils.test.ts
```

---

## 4. Das Datenmodell (`models/`) — der Scanner-Vertrag

Diese Typen **müssen** exakt zum JSON-Export des Scanners passen. Sie sind gegen
`scanner/src/json_dumper/dump.py` verifiziert.

### `organization.ts`

```ts
export type SovereigntyLevel =
  'sehr-hoch' | 'hoch' | 'mittel' | 'niedrig' | 'sehr-niedrig' | 'unbekannt'

export type MailSystemRole = 'smtp_out' | 'smtp_in' | 'imap_pop3' | 'webmailer'

export interface MailSystem {
  software: string | null
  vendor: string | null
  vendor_country: string | null
  vendor_country_rating: number | null
  vendor_category: string | null
  vendor_category_rating: number | null
  open_source_rating: number | null
  countries: string[]            // ISO-2-Codes der Hosting-IPs (distinkt, sortiert)
  hosters: string[]              // ASN-Org-Strings (distinkt, sortiert)
  proxy: MailSystem | null       // vorgeschaltetes Relay; proxy.proxy ist stets null
}

export type MailSystems = Record<MailSystemRole, MailSystem[]>

export interface Organization {
  org: string
  domain: string | null
  email_domain: string | null
  category: string               // 'hospital' | 'university' | 'city' | 'courthouse' | …
  wikidata_url: string | null
  city: string | null
  state: string | null
  country: string | null         // Rohlabel, z. B. 'Deutschland'
  lat: number | null
  long: number | null
  last_checked: string | null    // ISO 8601
  sovereignty_index: number | null   // 1=am souveränsten … 6=am wenigsten; null=unbewertet
  providers: string[]            // distinkte Vendor-Namen
  hosters: string[]              // distinkte ASN-Org-Strings
  mail_systems: MailSystems
}

export type MappableOrganization = Organization & { lat: number; long: number }
```

### `statisticsData.ts`

```ts
export interface StatisticsData {
  overview: Overview
  topMailVendors: Share[]
  topHosters: Share[]
}
export interface Overview {
  orgsScanned: number
  domainsScanned: number
  sovereigntyIndex: number   // Durchschnittsnote, z. B. 2.33
}
export interface Share { name: string; share: number }   // share ist ein Anteil 0..1
```

> Das `mail_systems`-Objekt trägt stets alle vier Rollen, aber `webmailer` wird vom
> aktuellen Scanner nie befüllt.

---

## 5. Score-Interpretation im Frontend (`utils/sovereignty.ts`)

Die Note (1–6) wird auf ein Label und eine Farbe abgebildet:

| Index | Level (`SovereigntyLevel`) | Farbe |
|---|---|---|
| 1 | `sehr-hoch` | `#2f9e44` (grün) |
| 2 | `hoch` | `#74b816` |
| 3 | `mittel` | `#f2cc0c` |
| 4 | `niedrig` | `#f76707` |
| 5 | `sehr-niedrig` | `#e03131` |
| 6 | `sehr-niedrig` | `#c92a2a` (dunkelrot) |
| `null` | `unbekannt` | `#adb5bd` (grau) |

Beachte: **5 und 6 teilen sich das Level-Label `sehr-niedrig`**, haben aber
unterschiedliche Farben. `sovereigntyLevel(index)` und `sovereigntyColor(index)`
sind die Zugriffsfunktionen; `SOVEREIGNTY_LEGEND` (best→schlechtest) speist die
Kartenlegende.

---

## 6. Seiten (`pages/`)

- **`Dashboard.tsx`** — der Daten-Hub (siehe §2). Auf Modulebene importiert es
  statisch `organizations.json`, globt eager `data/[0-9]*.json`, sortiert die
  datierten Dateien absteigend (Pfade mit `EXAMPLE` ausgeschlossen) und stellt
  `currentData`/`previousData` bereit. Rendert `Navbar`, `OverviewSection`,
  `InsightsSection`, `MapView`, `OrgTable`, `Footer`.
- **`LandingPage.tsx`** — statisch: `Navbar`, `Hero`, `SovereigntySection`,
  `FeaturesSection`, `Footer`.
- **`ScoreInfo.tsx`** — importiert
  `../../../Souveränitätsindex_V2_Spezifikation.md?raw` (die Spezifikation im
  Repo-Wurzelverzeichnis, ermöglicht durch `server.fs.allow: ['..']`) und rendert
  sie mit `react-markdown` + `remark-gfm`.

---

## 7. Komponenten (`components/`)

Jede Komponente hat ihre eigene `*.module.scss`; Farben sind als Hex hartkodiert
(keine Mantine-CSS-Variablen), gemäß der Styling-Konvention des Projekts.

### landing/

| Komponente | i18n-NS | Hinweise |
|---|---|---|
| `Hero` | `hero` | Vollflächiges Banner, CTA `<Link to="/dashboard">`, Scroll-Anker `#hintergrund`. |
| `Navbar` | `navbar` | Marke + `NavLink`s (`/`, `/dashboard`, `/score-info`) + `<LanguageSwitch />`. |
| `FeaturesSection` | `features` | Drei Feature-Karten (Tabler-Icons). |
| `SovereigntySection` | `sovereignty` | `id="hintergrund"` (Scroll-Ziel des Hero); Text + Highlight-Karten. |
| `Footer` | `footer` | Marke + Kontakt (Link zu audriga). |

### map/

| Komponente | Hinweise |
|---|---|
| `MapView` | Props `{ orgs, filters }`. Patcht Leaflets Default-Marker-Icons. `MapContainer` zentriert auf `[51.16, 10.45]` Zoom 6, **CARTO-light**-Tiles. Rendert `SearchControl`, `ClusteredMarkers` (nur Orgs mit lat/long), `Legend`, einen Filter-Toggle (mit Active-Count-Badge) und `FilterPanel`. **`FilterPanel` erhält die ungefilterten `orgs`**, damit seine Optionslisten vollständig bleiben. |
| `ClusteredMarkers` | Props `{ orgs: MappableOrganization[] }`. Gibt `null` zurück; baut imperativ eine `L.markerClusterGroup`. Jeder Marker hat einen farbigen SVG-Pin (`sovereigntyColor`) und ein **HTML-String-Popup** (kein React) mit Name, Domain, Kategorie, der Souveränitätszeile `"<level> (<index>/6)"`, einer Mail-Flow-Aufschlüsselung je Rolle (Vendor-Kategorie-Farbpille + Länderflaggen + optionale Proxy-„via …“-Zeile) und `last_checked` im Format `DD.MM.YYYY HH:mm`. Alle dynamischen Strings laufen durch `escapeHtml`. |
| `FilterPanel` | Props `{ orgs, selected, open, onToggle, onReset, onClose }`. Einschiebbares Akkordeon. Optionslisten aus `optionsFor`: `country` → fest `['Deutschland','Schweiz','Österreich']`; andere Felder → distinkte Werte aus `orgs`. |
| `Legend` | Rendert `SOVEREIGNTY_LEGEND` (6 farbige Pins, best→schlechtest). |
| `SearchControl` | Gibt `null` zurück; fügt eine `leaflet-geosearch`-Leiste hinzu (OpenStreetMap-Provider). |

### statistics/

| Komponente | Hinweise |
|---|---|
| `OverviewSection` | Props `{ currentData, previousData? }`. Rendert `StatisticsGrid` + `TopShares`. |
| `StatisticsGrid` | Baut drei `StatCard`s aus `currentData.overview`: orgsScanned, sovereigntyIndex (`isReversed` — niedriger ist besser), domainsScanned. Diff = `getDiffOrZero(current, previous)`. |
| `StatCard` | Präsentational. Zeigt Wert + vorzeichenbehaftete Differenz mit ↑/↓; Farbe kippt bei `isReversed`. |
| `TopShares` | Zwei Balkenlisten (`topMailVendors`, `topHosters`); Balkenbreite = `share*100%`. |
| `InsightsSection` | Props `{ orgs }`. Drei clientseitige Aggregationen als Balkenlisten: **Score-Verteilung** (`scoreHistogram`), **Ø-Souveränität je Sektor** (`sovereigntyBySector`), **Hosting-Residenz** (`hostingResidency`). |

### table/

| Komponente | Hinweise |
|---|---|
| `OrgTable` | Props `{ orgs, filters }` (erhält die bereits gefilterten `filters.filteredOrgs`). Freitextsuche über alle Spalten-Accessoren, `PAGE_SIZE = 10`-Pagination mit Ellipsis. Rendert `FilterChips`, ein Suchfeld, die Tabelle, einen Leerzustand und die Pagination. |
| `FilterChips` | Entfernbare Chips für jeden gewählten Filterwert + Alles-löschen. Gibt `null` zurück, wenn keine Filter aktiv sind. |
| `tableColumns` | Die `TABLE_COLUMNS`-Definition (8 Spalten): Domain, Org, Kategorie, Provider, Software, **Klasse** (schlechteste Vendor-Kategorie als farbiges Badge), **Hosting** (Länderflaggen), **Status** (Souveränitätslevel), Score. Jede Spalte hat einen typisierten `labelKey` und einen `accessor`; manche ein `render`. |

### common/

- **`LanguageSwitch`** — zwei `aria-pressed`-Toggle-Buttons (`DE`/`EN`); beim Klick
  `changeInterfaceLanguage(lang)`.

---

## 8. Aggregations-Engine (`utils/`)

| Util | Verantwortung |
|---|---|
| `sovereignty.ts` | Note → Level + Farbe (siehe §5); `SOVEREIGNTY_LEGEND`. |
| `mailInsights.ts` | Herzstück der Dashboard-Aggregationen: `VENDOR_CATEGORY_META` (Kategorie → i18n-Key + Farbe), `worstVendorCategory(org)`, `hostingCountries(org)` (Vereinigung aus System- + Proxy-Ländern), `roleGroups(org)` (für Popups), `scoreHistogram(orgs)` (6 Buckets), `sovereigntyBySector(orgs)`, `hostingResidency(orgs)`. |
| `countryUtils.ts` | `EU_EEA_CH`-Menge, `countryTier(code)` → `de/eu/other/us`, `worstTier(codes)`, `tierColor(tier)`. Spiegelt das Länder-Rating des Scanners. |
| `categoryUtils.ts` | `categoryLabel(t, category)`, `COUNTRY_FILTER_VALUES`, `countryFilterLabel(t, value)`. |
| `statisticsUtils.ts` | `getDiffOrZero(current, previous?)`, `selectByDiff(...)` — die unit-getesteten Helfer. |
| `translationUtils.ts` | `getCurrentLocale()`, `changeInterfaceLanguage(lang)` (persistiert in `localStorage['smart_lang']`). |

---

## 9. Filterung (`hooks/useOrgFilters.ts`, `constants/filterFields.ts`)

Drei Filterfelder werden angeboten:

```ts
FILTER_FIELDS = [
  { key: 'providers', labelKey: 'providerLabel', isArray: true  },
  { key: 'category',  labelKey: 'categoryLabel', isArray: false },
  { key: 'country',   labelKey: 'countryLabel',  isArray: false },
]
```

`useOrgFilters(orgs)` liefert `{ selected, filteredOrgs, activeCount, toggle, reset }`:

- Eine Org passt, wenn **für jedes Feld mit Auswahl** ihr Wert passt. Array-Felder
  (`providers`) passen, wenn ein Element gewählt ist (ODER innerhalb eines Felds);
  Skalarfelder passen, wenn der Wert gewählt ist. Verschiedene Felder werden mit
  **UND** verknüpft. Eine leere Auswahl in einem Feld setzt keine Einschränkung.
- `activeCount` ist die Gesamtzahl gewählter Werte; `toggle(key, value)`
  fügt hinzu/entfernt; `reset()` löscht alles.

Die eine Hook-Instanz lebt in `Dashboard` und wird von `MapView`, `FilterPanel`,
`OrgTable` und `FilterChips` geteilt.

---

## 10. Internationalisierung (`i18n/`)

- `i18n.ts` initialisiert i18next mit `defaultNS = 'common'`, `lng` aus
  `localStorage['smart_lang']` (Default `de`), `fallbackLng: 'de'`,
  `interpolation.escapeValue: false`, `initImmediate: false` (synchron).
- `resources.ts` setzt `{ en, de }` zusammen, jeweils mit den **10 Namespaces** zu
  ihrem Locale-Modul; `de` ist als `typeof en` typisiert, sodass beide Sprachen zur
  Compile-Zeit strukturell identisch bleiben.
- `i18next.d.ts` erweitert die i18next-Typen, sodass `t()`-Keys vollständig
  typgeprüft sind.
- **Namespaces:** `common`, `navbar`, `hero`, `sovereignty`, `features`, `footer`,
  `statistics`, `map`, `mail`, `table`. Locale-Dateien unter
  `i18n/locales/{de,en}/<namespace>.ts`.
- **Sprachumschaltung:** nur `de` und `en`, Deutsch ist Default und Fallback.

---

## 11. Datendateien (`data/`)

| Datei | Typ | Verwendung |
|---|---|---|
| `organizations.json` | `Organization[]` (~5 k Einträge) | statisch von `Dashboard` importiert, unbewertete Orgs herausgefiltert |
| `<YYYY-MM-DD>.json` | `StatisticsData` | per Glob importiert, neueste = `currentData`, zweitneueste = `previousData` (treibt „seit letztem Scan“-Differenzen) |

Beide werden vom `dump.py` des Scanners erzeugt. Zum Aktualisieren der Site den
Scanner-Export nach `data/` kopieren und neu bauen. Jeder Pfad mit `EXAMPLE` wird
vom Glob ignoriert.

---

## 12. Build, CI/CD & Deployment

- **`vite.config.ts`** — `base = process.env.BASE_PATH || '/'`; React Compiler via
  Babel-Preset; `server.fs.allow: ['..']` (damit `ScoreInfo` die Spezifikation im
  Repo-Wurzelverzeichnis importieren kann); Coverage-Reporter `lcov`. Pfad-Aliase
  `@assets`, `@components`, `@constants`, `@hooks`, `@models`, `@pages`, `@utils`
  (gespiegelt in `tsconfig.app.json`).
- **`.github/workflows/deploy.yml`** — bei Push auf `main` mit Änderungen an
  `frontend/**`: Node 22, `npm ci`, `npm run build` mit `BASE_PATH=/<repo-name>/`,
  `dist/index.html` → `dist/404.html` kopieren (SPA-Fallback fürs Client-Routing),
  Deploy auf GitHub Pages.
- **`.github/workflows/ci.yml`** — Lint + Build bei PR/Push, plus `vitest run
  --coverage` für SonarQube (lcov unter `frontend/coverage/lcov.info`).
- **Husky** (`.husky/pre-commit`) führt `lint-staged` nur aus, wenn gestagte Pfade
  mit `frontend/` beginnen (Prettier + ESLint --fix auf TS/TSX; Prettier auf
  CSS/JSON).

---

## 13. Tests (`__tests__/`)

Die einzige Frontend-Testdatei ist **`statisticsUtils.test.ts`** (Vitest), sie deckt
`getDiffOrZero` und `selectByDiff` ab. Die reichere Aggregationslogik in
`mailInsights.ts`, `sovereignty.ts`, `countryUtils.ts` und `useOrgFilters.ts` ist
**noch nicht** unit-getestet — ein guter Ansatzpunkt, die Abdeckung zu erweitern.
Start mit `npm test`.

---

## 14. Wissenswertes für Betreuer

- Die Daten werden **in `Dashboard.tsx` auf Modulebene** geladen; es gibt **keinen
  React-Context** — reine Props + eine geteilte `useOrgFilters`-Hook.
- **Kein `@mantine/charts`** — alle Charts/Balken sind handgebaute `<div>`s.
- Die Karten-**Popups sind rohe HTML-Strings** (mit manuellem `escapeHtml`), kein
  React.
- Die Souveränitätsskala ist **1 (best) … 6 (schlechtest)**; `null` = unbewertet;
  **die Level 5 und 6 bilden beide auf `sehr-niedrig` ab**.
- Der **React Compiler ist aktiviert** — Muster vermeiden, die seine Annahmen
  unterlaufen.
- Der GitHub-Pages-Basispfad wird über `BASE_PATH` → `vite base` +
  `BrowserRouter basename` injiziert; `404.html` liefert den SPA-Fallback.
