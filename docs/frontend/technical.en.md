# S.M.A.R.T. Frontend — Technical Documentation (EN)

The frontend is a **Vite + React 19 + TypeScript** single-page application that
visualises the digital-sovereignty data produced by the scanner. It renders a
landing page, an interactive map, a statistics dashboard, a filterable table, and a
scoring-methodology page. It is a **static site** (all data bundled at build time)
deployed to **GitHub Pages**.

Non-technical usage: [user.en.md](user.en.md). German version:
[technical.de.md](technical.de.md).

---

## 1. Technology stack

| Concern | Choice |
|---|---|
| Build tool | **Vite 8** (`@vitejs/plugin-react`) |
| UI library | **React 19** + **React Compiler** (Babel preset, enabled in `vite.config.ts`) |
| Component kit | **Mantine 9** (`@mantine/core`, `@mantine/hooks`) — provider + theme; most layout is bespoke SCSS |
| Map | **Leaflet 1.9** + **react-leaflet 5** + `leaflet.markercluster` + `leaflet-geosearch` |
| Routing | **react-router-dom 7** (`BrowserRouter`) |
| i18n | **i18next 25** + **react-i18next 16** (German default, English alternative) |
| Icons | `@tabler/icons-react`; country flags via `flag-icons` CSS |
| Markdown | `react-markdown` + `remark-gfm` (renders the score spec) |
| Dates | `dayjs` (map popups) |
| Styling | **SCSS modules** (`sass-embedded`), one `*.module.scss` per component |
| Tests | **Vitest 4** (+ `@vitest/coverage-v8`) |
| Lint/format | ESLint 9 (flat config) + Prettier (with import-sort plugin) |
| Git hooks | **Husky** + **lint-staged** (pre-commit) |

There is **no** `@mantine/charts` dependency; all bars/histograms are hand-rolled
`<div>`s with inline `width`/`background`.

### Scripts (`package.json`)

| Script | Command | Purpose |
|---|---|---|
| `dev` | `vite` | dev server (http://localhost:5173) |
| `build` | `tsc -b && vite build` | type-check then build |
| `lint` | `eslint .` | lint |
| `test` | `vitest` | run tests |
| `preview` | `vite preview` | preview a production build |
| `format` | `prettier --write "src/**/*.{ts,tsx,css}"` | format |

---

## 2. Architecture: bootstrap, routing, data flow

### Bootstrap — `src/main.tsx`

```
<StrictMode>
  <MantineProvider theme={theme} defaultColorScheme="light">
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <App />
```

Side-effect imports here initialise the app: `flag-icons` CSS, Mantine CSS, and
**`./i18n/i18n`** (i18next initialises synchronously at import time). The
`BrowserRouter` `basename` is the GitHub-Pages base path.

### Routing — `src/App.tsx`

`App` is *only* a route table — **no data loading and no context providers**:

| Path | Page |
|---|---|
| `/` | `LandingPage` |
| `/dashboard` | `Dashboard` |
| `/score-info` | `ScoreInfo` |

### Data flow (important)

Data is loaded **at module scope inside `Dashboard.tsx`**, not in `App.tsx`, and
there is **no React Context** — everything is passed as props. A single
`useOrgFilters` hook instance (created in `Dashboard`) is shared between the map and
the table so they stay in sync.

```
src/data/organizations.json  ──static import──┐
src/data/<date>.json (import.meta.glob, eager) │
                                               ▼
                              Dashboard.tsx (module scope)
   organizations = organizationsData.filter(hasMailSystems)   // orgs with ≥1 mail system
   currentData / previousData = newest / 2nd-newest dated overview file
                                               │
            useOrgFilters(organizations) ──────┤
                                               ▼
   <OverviewSection currentData previousData />     (stat cards + top shares)
   <InsightsSection orgs={organizations} />         (histograms computed client-side)
   <MapView orgs filters />                         (Leaflet + clusters + popups)
   <OrgTable orgs={filters.filteredOrgs} filters /> (search + pagination)
```

Organisations are dropped only when **no mail system was found** for them
(`hasMailSystems`). Unrated organisations (`sovereignty_index == null`) that still
have mail infrastructure — e.g. a known hoster but unidentified software — **are
shown** (grey / "unbekannt"); they are only left out of the grade-based statistics.
The frontend never fetches at runtime — all JSON is bundled by Vite.

### Theme — `src/theme.ts`

Mantine `createTheme`: `primaryColor: 'green'`, Inter font, `defaultRadius: 'md'`, a
custom 10-shade green palette, and a default making all `Paper` white.

---

## 3. Project layout

```
frontend/src/
├── main.tsx · App.tsx · theme.ts
├── pages/
│   ├── Dashboard.tsx          # data hub: loads JSON, wires sections
│   ├── LandingPage.tsx        # marketing page (no data)
│   └── ScoreInfo.tsx          # renders the V2 spec markdown
├── components/
│   ├── landing/   Hero · Navbar · FeaturesSection · SovereigntySection · Footer
│   ├── map/       MapView · ClusteredMarkers · FilterPanel · Legend · SearchControl
│   ├── statistics/ OverviewSection · StatisticsGrid · StatCard · TopShares · VendorClassChart · InsightsSection
│   ├── table/     OrgTable · FilterChips · tableColumns
│   └── common/    LanguageSwitch
├── models/        organization.ts · statisticsData.ts     # the scanner contract
├── utils/         sovereignty · statisticsUtils · mailInsights · categoryUtils · countryUtils · translationUtils
├── hooks/         useOrgFilters.ts
├── constants/     filterFields.ts
├── i18n/          i18n.ts · resources.ts · i18next.d.ts · locales/{de,en}/<ns>.ts
├── data/          organizations.json · <date>.json        # scanner export
└── __tests__/     statisticsUtils · mailInsights · sovereignty · countryUtils · categoryUtils (.test.ts)
```

---

## 4. The data model (`models/`) — the scanner contract

These types **must** match the scanner's JSON export exactly. They are verified
against `scanner/src/json_dumper/dump.py`.

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
  countries: string[]            // ISO-2 codes of hosting IPs (distinct, sorted)
  hosters: string[]              // ASN org strings (distinct, sorted)
  proxy: MailSystem | null       // security relay in front; proxy.proxy is always null
}

export type MailSystems = Record<MailSystemRole, MailSystem[]>

export interface Organization {
  org: string
  domain: string | null
  email_domain: string | null
  category: string               // 'hospital' | 'university' | 'city' | 'courthouse' | 'newspaper' | 'political party'
  wikidata_url: string | null
  city: string | null
  state: string | null
  country: string | null         // raw label, e.g. 'Deutschland'
  lat: number | null
  long: number | null
  last_checked: string | null    // ISO 8601
  sovereignty_index: number | null   // 1=most sovereign … 6=least; null=unrated
  providers: string[]            // distinct vendor names
  hosters: string[]              // distinct ASN org strings
  mail_systems: MailSystems
}

export type MappableOrganization = Organization & { lat: number; long: number }
```

### `statisticsData.ts`

```ts
export interface StatisticsData {
  overview: Overview
  topHosters: Share[]
}
export interface Overview {
  orgsScanned: number
  domainsScanned: number
  sovereigntyIndex: number   // average grade, e.g. 2.33
}
export interface Share { name: string; share: number }   // share is a fraction 0..1
```

> The `mail_systems` object always carries all four roles, but `webmailer` is
> never populated by the current scanner.

---

## 5. Score interpretation on the frontend (`utils/sovereignty.ts`)

The grade (1–6) is mapped to a label and a colour:

| index | level (`SovereigntyLevel`) | colour |
|---|---|---|
| 1 | `sehr-hoch` | `#2f9e44` (green) |
| 2 | `hoch` | `#74b816` |
| 3 | `mittel` | `#f2cc0c` |
| 4 | `niedrig` | `#f76707` |
| 5 | `sehr-niedrig` | `#e03131` |
| 6 | `sehr-niedrig` | `#c92a2a` (dark red) |
| `null` | `unbekannt` | `#adb5bd` (grey) |

Note that **5 and 6 share the level label `sehr-niedrig`** but have different
colours. `sovereigntyLevel(index)` and `sovereigntyColor(index)` are the accessors;
`SOVEREIGNTY_LEGEND` (best→worst) drives the map legend.

---

## 6. Pages (`pages/`)

- **`Dashboard.tsx`** — the data hub (see §2). At module scope it statically imports
  `organizations.json` and eagerly globs `data/[0-9]*.json`, sorts the dated files
  descending (excluding any path containing `EXAMPLE`), and exposes
  `currentData`/`previousData`. Renders `Navbar`, `OverviewSection`,
  `InsightsSection`, `MapView`, `OrgTable`, `Footer`.
- **`LandingPage.tsx`** — static: `Navbar`, `Hero`, `SovereigntySection`,
  `FeaturesSection`, `Footer`.
- **`ScoreInfo.tsx`** — imports `../../../Souveränitätsindex_V2_Spezifikation.md?raw`
  (the repo-root spec, enabled by `server.fs.allow: ['..']`) and renders it with
  `react-markdown` + `remark-gfm`.

---

## 7. Components (`components/`)

Every component has its own `*.module.scss`; colours are hard-coded hex (no Mantine
CSS variables), per the project's styling convention.

### landing/

| Component | i18n ns | Notes |
|---|---|---|
| `Hero` | `hero` | Full-bleed banner, CTA `<Link to="/dashboard">`, scroll anchor `#hintergrund`. |
| `Navbar` | `navbar` | Brand + `NavLink`s (`/`, `/dashboard`, `/score-info`) + `<LanguageSwitch />`. |
| `FeaturesSection` | `features` | Three feature cards (Tabler icons). |
| `SovereigntySection` | `sovereignty` | `id="hintergrund"` (Hero scroll target); copy + highlight cards. |
| `Footer` | `footer` | Brand + contact (links to audriga). |

### map/

| Component | Notes |
|---|---|
| `MapView` | Props `{ orgs, filters }`. Patches Leaflet's default marker icons. `MapContainer` centred on `[51.16, 10.45]` zoom 6, **CARTO light** tiles. Renders `SearchControl`, `ClusteredMarkers` (only orgs with lat/long), `Legend`, a filter toggle (with active-count badge), and `FilterPanel`. **`FilterPanel` receives the unfiltered `orgs`** so its option lists stay complete. |
| `ClusteredMarkers` | Props `{ orgs: MappableOrganization[] }`. Returns `null`; imperatively builds an `L.markerClusterGroup`. Each marker has a coloured SVG pin (`sovereigntyColor`) and an **HTML-string popup** (not React) with name, domain, category, the sovereignty line `"<level> (<index>/6)"`, a per-role mail-flow breakdown (vendor-category colour pill + country flags + optional proxy "via …" line), and `last_checked` formatted `DD.MM.YYYY HH:mm`. All dynamic strings pass through `escapeHtml`. |
| `FilterPanel` | Props `{ orgs, selected, open, onToggle, onReset, onClose }`. Slide-in accordion. Option lists from `optionsFor`: `country` → fixed `['Deutschland','Schweiz','Österreich']`; other fields → distinct values harvested from `orgs`. |
| `Legend` | Renders `SOVEREIGNTY_LEGEND` (6 coloured pins, best→worst). |
| `SearchControl` | Returns `null`; adds a `leaflet-geosearch` bar (OpenStreetMap provider). |

### statistics/

| Component | Notes |
|---|---|
| `OverviewSection` | Props `{ currentData, previousData?, orgs }`. Renders `StatisticsGrid` + `TopShares`. |
| `StatisticsGrid` | Builds three `StatCard`s from `currentData.overview`: orgsScanned, sovereigntyIndex (`isReversed` — lower is better), domainsScanned. Diff = `getDiffOrZero(current, previous)`. |
| `StatCard` | Presentational. Shows value + signed diff with ↑/↓; colour flips when `isReversed`. |
| `TopShares` | Props `{ orgs, hosters }`. Renders `VendorClassChart` (vendor-class donut, computed client-side) + a `topHosters` bar list (bar width = `share*100%`). |
| `VendorClassChart` | Props `{ orgs }`. SVG donut of `vendorClassDistribution(orgs)` — the worst vendor class per org, unidentified vendors falling into "Unknown". |
| `InsightsSection` | Props `{ orgs }`. Three client-side aggregations rendered as bar lists: **score distribution** (`scoreHistogram`, plus an appended **"Ungraded"** bar counting `sovereignty_index == null` orgs), **avg sovereignty by sector** (`sovereigntyBySector`), **hosting residency** (`hostingResidency`). |

### table/

| Component | Notes |
|---|---|
| `OrgTable` | Props `{ orgs, filters }` (receives the already-filtered `filters.filteredOrgs`). Free-text search across all column accessors, `PAGE_SIZE = 10` pagination with ellipsis. Renders `FilterChips`, a search box, the table, an empty state, and pagination. |
| `FilterChips` | Removable chips for every selected filter value + clear-all. Returns `null` when no filters active. |
| `tableColumns` | The `TABLE_COLUMNS` definition (9 columns): Domain, Org, Category, Provider, Software, **Class** (worst vendor category as a coloured badge), **Hosting** (country flags), **Status** (sovereignty level), Score. Each column has a typed `labelKey` and an `accessor`; some have a `render`. |

### common/

- **`LanguageSwitch`** — two `aria-pressed` toggle buttons (`DE`/`EN`); on click calls
  `changeInterfaceLanguage(lang)`.

---

## 8. Aggregation engine (`utils/`)

| Util | Responsibility |
|---|---|
| `sovereignty.ts` | Grade → level + colour (see §5); `SOVEREIGNTY_LEGEND`. |
| `mailInsights.ts` | The heart of the dashboard aggregations: `VENDOR_CATEGORY_META` + `vendorCategoryMeta` (category → i18n key + colour), `worstVendorCategory(org)`, `hasMailSystems(org)` (dashboard inclusion filter), `hostingCountries(org)` (union of system + proxy countries), `roleGroups(org)` (for popups), `scoreHistogram(orgs)` (6 buckets), `sovereigntyBySector(orgs)`, `hostingResidency(orgs)`, `vendorClassDistribution(orgs)`. |
| `countryUtils.ts` | `EU_EEA_CH` set, `countryTier(code)` → `de/eu/other/us`, `worstTier(codes)`, `tierColor(tier)`. Mirrors the scanner's country rating. |
| `categoryUtils.ts` | `categoryLabel(t, category)` + `CATEGORY_KEYS`, `vendorClassLabel(t, key)`, `COUNTRY_FILTER_VALUES`, `countryFilterLabel(t, value)`. |
| `statisticsUtils.ts` | `getDiffOrZero(current, previous?)`, `selectByDiff(...)` — the unit-tested helpers. |
| `translationUtils.ts` | `getCurrentLocale()`, `changeInterfaceLanguage(lang)` (persists to `localStorage['smart_lang']`). |

---

## 9. Filtering (`hooks/useOrgFilters.ts`, `constants/filterFields.ts`)

Four filter fields are exposed, each with an `accessor(org)`:

```ts
FILTER_FIELDS = [
  { key: 'providers',   labelKey: 'providerLabel',    accessor: org => org.providers },
  { key: 'vendorClass', labelKey: 'vendorClassLabel', accessor: org => vendorCategoryMeta(worstVendorCategory(org)).key },
  { key: 'category',    labelKey: 'categoryLabel',    accessor: org => org.category },
  { key: 'country',     labelKey: 'countryLabel',     accessor: org => org.country },
]
```

`useOrgFilters(orgs)` returns `{ selected, filteredOrgs, activeCount, toggle, reset }`:

- An org passes if, **for every field that has selections**, its value matches.
  Array fields (`providers`) match if any element is selected (OR within a field);
  scalar fields match if the value is selected. Different fields are combined with
  **AND**. An empty selection on a field imposes no constraint.
- `activeCount` is the total number of selected values; `toggle(key, value)`
  adds/removes; `reset()` clears all.

The single hook instance lives in `Dashboard` and is shared by `MapView`,
`FilterPanel`, `OrgTable` and `FilterChips`.

---

## 10. Internationalisation (`i18n/`)

- `i18n.ts` initialises i18next with `defaultNS = 'common'`, `lng` from
  `localStorage['smart_lang']` (default `de`), `fallbackLng: 'de'`,
  `interpolation.escapeValue: false`, `initImmediate: false` (synchronous).
- `resources.ts` assembles `{ en, de }`, each mapping the **10 namespaces** to its
  locale module; `de` is typed as `typeof en` so the two languages are kept
  structurally identical at compile time.
- `i18next.d.ts` augments i18next's types so `t()` keys are fully type-checked.
- **Namespaces:** `common`, `navbar`, `hero`, `sovereignty`, `features`, `footer`,
  `statistics`, `map`, `mail`, `table`. Locale files live under
  `i18n/locales/{de,en}/<namespace>.ts`.
- **Language switching:** only `de` and `en`, German is default and fallback.

---

## 11. Data files (`data/`)

| File | Type | Use |
|---|---|---|
| `organizations.json` | `Organization[]` (~5 k entries) | statically imported by `Dashboard`, filtered to orgs with ≥1 mail system (`hasMailSystems`) |
| `<YYYY-MM-DD>.json` | `StatisticsData` | glob-imported, newest = `currentData`, 2nd-newest = `previousData` (drives "since last scan" diffs) |

Both are produced by the scanner's `dump.py`. To update the site, copy the scanner
export into `data/` and rebuild. Any file path containing `EXAMPLE` is ignored by
the glob.

---

## 12. Build, CI/CD & deployment

- **`vite.config.ts`** — `base = process.env.BASE_PATH || '/'`; React Compiler via
  Babel preset; `server.fs.allow: ['..']` (so `ScoreInfo` can import the repo-root
  spec); coverage reporter `lcov`. Path aliases `@assets`, `@components`,
  `@constants`, `@hooks`, `@models`, `@pages`, `@utils` (mirrored in
  `tsconfig.app.json`).
- **`.github/workflows/deploy.yml`** — on push to `main` touching `frontend/**`:
  Node 22, `npm ci`, `npm run build` with `BASE_PATH=/<repo-name>/`, copy
  `dist/index.html` → `dist/404.html` (SPA fallback for client routing), deploy to
  GitHub Pages.
- **`.github/workflows/ci.yml`** — lint + build on PR/push, plus `vitest run
  --coverage` feeding SonarQube (lcov at `frontend/coverage/lcov.info`).
- **Husky** (`.husky/pre-commit`) runs `lint-staged` only when staged paths begin
  with `frontend/` (Prettier + ESLint --fix on TS/TSX; Prettier on CSS/JSON).

---

## 13. Testing (`__tests__/`)

Vitest unit tests live in `__tests__/`: **`statisticsUtils`** (`getDiffOrZero`,
`selectByDiff`), **`mailInsights`** (aggregations incl. `hasMailSystems`,
`hostingResidency`, `vendorClassDistribution`), **`sovereignty`**, **`countryUtils`**
and **`categoryUtils`**. `useOrgFilters.ts` is not yet covered — a good area to
extend. Run with `npm test`.

---

## 14. Notable facts for maintainers

- Data is loaded **in `Dashboard.tsx` at module scope**; there is **no React
  Context** — pure props + one shared `useOrgFilters` hook.
- **No `@mantine/charts`** — all charts/bars are hand-built `<div>`s.
- The map **popups are raw HTML strings** (with manual `escapeHtml`), not React.
- The sovereignty scale is **1 (best) … 6 (worst)**; `null` = unrated; **levels 5
  and 6 both map to `sehr-niedrig`**.
- The **React Compiler is enabled** — avoid patterns that defeat its assumptions.
- GitHub Pages base path is injected via `BASE_PATH` → `vite base` +
  `BrowserRouter basename`; `404.html` provides the SPA fallback.
