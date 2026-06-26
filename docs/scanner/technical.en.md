# S.M.A.R.T. Scanner — Technical Documentation (EN)

> **S.M.A.R.T.** = **S**overeign **M**ail **A**ssessment and **R**ating **T**ool.
> The scanner discovers the mail infrastructure of public-sector organisations in
> the DACH region (Germany, Austria, Switzerland), fingerprints the products and
> vendors involved, derives a digital-sovereignty grade per organisation, and
> exports the result as JSON for the frontend.

This document describes the scanner as it is actually implemented. For the
non-technical operating instructions see [user.en.md](user.en.md). For the German
version see [technical.de.md](technical.de.md).

---

## 1. What the scanner does

For every organisation it knows about, the scanner answers the question:

> *Is this organisation's e-mail run on sovereign (EU / public-sector / open)
> infrastructure, or does it depend on foreign hyperscalers such as Microsoft 365
> or Google Workspace?*

It does this by:

1. building a list of organisations and their domains from **Wikidata**;
2. resolving each domain's **MX / IP / ASN / PTR / SMTP / IMAP** records;
3. **fingerprinting** the mail products and vendors via regex signatures;
4. storing everything in a **versioned SQLite schema** (one row per scan run);
5. computing the **Souveränitätsindex V2** (sovereignty index, grade 1–6);
6. **exporting** a slim JSON document plus an aggregate overview.

The output scale is a school-grade scale: **1 = very sovereign … 6 = not
sovereign**, `null` = could not be rated.

---

## 2. End-to-end data flow

```
                 ┌─────────────────────────────────────────────────────────┐
                 │  Wikidata (QLever SPARQL)  +  website e-mail scraper      │
                 └───────────────────────────┬─────────────────────────────┘
                                             │  organisations + domains
                                             ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  SQLite:  organisations · org_domain_history                       │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  current domains
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Scan pipeline (async):  MX → IP → ASN → PTR / SMTP / IMAP / SPF   │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  raw observations (pandas frames)
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Signature matcher:  MX host / SMTP banner / IMAP banner → vendor  │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  detections
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  to_db:  mail_systems · ip_addresses · *_history link tables       │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  scored structure
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Sovereignty index calc  +  JSON dump (+ Brotli)                   │
        └───────────────────────────┬──────────────────────────────────────┘
                                     ▼
              database/export/organizations.json   (per-org detail)
              database/export/<YYYY-MM-DD>.json     (aggregate overview)
```

The domain-list build (step 0) is run **separately** and on demand. `main.py`
runs only steps **scan → to_db → dump** against the domains already in the
database.

---

## 3. Technology & requirements

| Concern | Choice |
|---|---|
| Language | Python **3.12+** (`.python-version` = `3.12`) |
| Package / venv manager | **uv** (`uv sync`, `uv run`) |
| Database | **SQLite** via **SQLAlchemy 2.0** ORM (declarative) |
| Async I/O | `asyncio`, `aiodns`, `dnspython` |
| Web scraping | **Scrapy** (e-mail scraper), `requests` (SPARQL) |
| Data wrangling | **pandas** |
| Compression | **Brotli** (export `.json.br`) |
| Tests | **pytest** (+ `pytest-cov`) |

Key runtime dependencies (`pyproject.toml`): `aiodns`, `brotli`, `dnspython`,
`ipwhois`, `overpy`, `pandas`, `pyyaml`, `requests`, `scrapy`, `sqlalchemy`.
Dev group: `pytest`, `pytest-cov`.

> **Note:** `tldextract` is imported by the domain-list pipeline but is not
> declared in `pyproject.toml`; it is currently resolved transitively. Add it
> explicitly if you tighten the lockfile.

---

## 4. Project layout

```
scanner/
├── main.py                       # entrypoint: scan → to_db → dump
├── pyproject.toml / uv.lock      # deps, locked
├── database/
│   ├── SMART.db                  # the working database
│   └── export/                   # JSON + Brotli output
└── src/
    ├── config.yml                # legacy rating config (NOT used at runtime)
    ├── db/
    │   ├── base.py               # engine/session, create_all, legacy migration
    │   ├── models.py             # ORM tables + rating enums/helpers
    │   ├── runs.py               # ScannerRun context manager, git hash
    │   └── history.py            # SCD-2 versioning engine (update_history)
    ├── domainlist_pipline/
    │   ├── config.yaml           # Wikidata institutions × areas (USED)
    │   ├── org_list_pipeline.py  # Wikidata/QLever fetch + persist
    │   └── email_scraper.py      # Scrapy crawl to fill missing email domains
    ├── scanner_pipeline/
    │   ├── step.py               # abstract async Step (one observation kind)
    │   ├── registry.py           # dependency-ordered step runner
    │   ├── asn_bulk.py           # Team Cymru bulk ASN/whois lookups
    │   └── to_db.py              # writes entities + history link tables
    ├── signatures_pipeline/
    │   ├── matcher.py            # load_signatures / match_signature
    │   ├── parse_signature.py    # signature linter/validator
    │   └── signatures/
    │       ├── mx.yaml           # matched against MX hostnames
    │       ├── smtp.yaml         # matched against SMTP banners
    │       └── imap.yaml         # matched against IMAP banners + host
    ├── json_dumper/
    │   ├── dump.py               # serialises orgs → JSON, builds overview
    │   └── sovereignty_index_calc.py   # the scoring algorithm
    └── enricher/                 # legacy prototype (NOT wired into main.py)
```

---

## 5. The entrypoint — `main.py`

`main.py` orchestrates a single scan run. There is no argument parsing; the only
knobs are two module-level constants:

```python
DB_NAME = "SMART.db"
SAMPLE_LIMIT: int | None = None   # set to an int to scan only N domains (testing)
```

`main(db_path=None, sample_limit=SAMPLE_LIMIT)` does:

1. Resolve the DB path (default `scanner/database/SMART.db`).
2. `make_engine` → `migrate_legacy_schema` → `create_all` → `make_session`.
3. Open a `scanner_run(session)` context (inserts a `ScannerRun` row, prints
   `run.id`).
4. **Scan** — `Registry.from_sqlite(db_path, _domain_query(sample_limit))`, then
   `asyncio.run(registry.run_queue())`.
5. **Persist** — `to_db(session, run, registry)`.
6. **Export** — `count = write_dump(session)`; prints the org count.

`_domain_query()` selects the domains to scan:

```sql
SELECT * FROM org_domain_history
WHERE is_current = 1
  AND (website_domain IS NOT NULL OR email_domain IS NOT NULL)
[ LIMIT N ]
```

Run it with `cd scanner && uv run main.py`.

---

## 6. Step 0 — Building the organisation/domain list

This stage populates `organisations` and `org_domain_history`. It is **not**
called by `main.py`; run it separately when you want to (re)build the org list.

### 6.1 Wikidata fetch — `org_list_pipeline.py`

- Queries the **QLever** Wikidata endpoint (`https://qlever.dev/api/wikidata`)
  over SPARQL, User-Agent `SMART-BOT/1.4`, with up to `MAX_ATTEMPTS = 3` retries.
- The set of entities fetched is driven by `domainlist_pipline/config.yaml`:

  ```yaml
  institutions:                 # Wikidata QIDs + extra SPARQL filters
    university: { qid: Q3918 }
    hospital:   { qid: Q16917 }
    school:     { qid: Q132050, filters: [ "FILTER NOT EXISTS { ?item wdt:P31/wdt:P279* wd:Q3918. }" ] }
    courthouse: { qid: Q41487 }
    city:       { qid: Q515 }
  areas:                        # which countries to cover
    germany: Q183
    austria: Q40
    switzerland: Q39
  ```

  The pipeline fetches the **cross-product** institution × area. Selected
  properties: label, website (`P856`), e-mail (`P968`), coordinates (`P625`),
  city / state / country (German labels).

- Normalisation helpers:
  - `extract_website_domain()` → registered domain via `tldextract`
    (`www.mannheim.de`, `en.mannheim.de` → `mannheim.de`).
  - `normalize_email_to_domain()` → lower-cased domain after the `@`.
- Persistence (`_persist_record`): `get_or_create(Organisation, wikidata_url=…)`,
  update scalar fields, then `update_history(OrgDomainHistory, …)` with tracked
  fields `email_domain` and `website_domain`. An existing e-mail domain is kept if
  Wikidata supplies none.

### 6.2 E-mail scraper — `email_scraper.py`

Fills `email_domain` for current orgs that still have none, using a **Scrapy**
spider (`mailto_spider`):

- Settings: `DOWNLOAD_TIMEOUT=12`, `ROBOTSTXT_OBEY=True`, `CONCURRENT_REQUESTS=16`,
  `CONCURRENT_REQUESTS_PER_DOMAIN=2`, `DOWNLOAD_DELAY=0.5`, UA `SMART-BOT/1.4`.
- If the org already has an `smtp_in` mail system, its `email_domain` is set to
  the `website_domain` directly (no crawl).
- Otherwise it crawls the homepage for `mailto:` addresses; if none are found it
  follows the first *Impressum*/*Kontakt* link once.
- Generic local parts (`noreply`, `webmaster`, `postmaster`, …) are ignored when
  picking a domain.

---

## 7. Step 1 — The scan pipeline (`scanner_pipeline/`)

The scan pipeline is an **async, dependency-ordered DAG** over pandas DataFrames.

### 7.1 What a "Step" is — `step.py`

`Step` is an abstract base class. Each concrete step consumes one column from the
output of its `required_step` and produces new rows.

- `input_col` — the column it reads.
- `required_step` — the step whose output it consumes.
- `async get(value) -> list[dict]` — the per-value work (one DNS/TCP probe etc.).
- Concurrency is bounded by an `asyncio.Semaphore` (default 20).
- `_run_task` wraps `get` in try/except and attaches an `error` field
  (`None` on success, the exception string on failure).
- `scan(data)` = `preprocess` (dropna + dedupe on `input_col`) → `get_func`
  (fan-out + progress monitor + flatten) → `postprocess` (dedupe).

### 7.2 The steps and their lineage

| Step | requires | input col | output columns | probe |
|---|---|---|---|---|
| `Domain` | — (seed) | — | `organisation_id, website_domain, email_domain` | DB rows |
| `Combiner` | `Domain` | — | `organisation_id, domain` | melts website+email into one `domain` |
| `MX` | `Combiner` | `domain` | `domain, mx_domain` | DNS MX |
| `IP` | `MX` | `mx_domain` | `mx_domain, ip` | `getaddrinfo` |
| `ASN` | `IP` | `ip` | `ip, asn, owner, country, error` | Team Cymru bulk WHOIS |
| `PTR` | `IP` | `ip` | `ip, ptr` | reverse DNS |
| `SMTP` | `MX` | `mx_domain` | `mx_domain, smtp_banner, port` | connect 25/587/465, read banner |
| `IMAP` | `Combiner` | `domain` | `domain, imap_host, port, banner` | hosts `imap/mail/webmail/exchange` × ports 143/993 |
| `SPF` | `Combiner` | `domain` | `domain, spf` | TXT records `v=spf1…` |

> `SPF` is collected but **not** persisted by `to_db.py` (see §13, Known gaps).

### 7.3 The registry — `registry.py`

`Registry` holds a `queue` of step instances and a `results` dict
`StepClass → DataFrame`.

- `run_queue()` repeatedly picks the first queued step whose `required_step`
  output already exists, runs it, stores the result, and removes it from the
  queue — so the queue is **self-ordering by dependency**.
- `from_sqlite(db, query)` seeds the `Domain` result by reading the DB query into
  a DataFrame, then enqueues all the other steps.

### 7.4 Bulk ASN lookup — `asn_bulk.py`

- `lookup_asn_bulk(ips)` talks to **Team Cymru** bulk WHOIS
  (`whois.cymru.com:43`) in batches of 1000, parses the pipe-delimited reply, and
  returns `{ip: {asn, asn_org, country_code}}`. Socket failures degrade
  gracefully (that batch is simply skipped).
- `enrich_ip_addresses(session, only_missing=True)` is a **recovery utility**: it
  re-runs the ASN lookup for `ip_addresses` rows (optionally only those missing
  `asn_org`), updates `asn`, `asn_org`, `country_code` and the derived
  `country_rating` / `asn_rating`, and commits. Use it after a scan that hit DNS
  rate limits, then re-run `write_dump`.

---

## 8. Step 2 — Signature matching (`signatures_pipeline/`)

Vendor/product fingerprinting from regex signatures.

### 8.1 The matcher — `matcher.py`

- `SIGNATURE_FIELDS` are the 8 fields a match contributes to a mail system:
  `software, role, vendor, vendor_country, vendor_category,
  vendor_country_rating, open_source_rating, vendor_category_rating`.
- `load_signatures(kind)` (LRU-cached) reads `signatures/<kind>.yaml` and compiles
  each entry's `regex`.
- `match_signature(kind, *texts)` returns the **first** signature whose pattern
  matches any of the texts (so **file order matters**), or `None`.

### 8.2 Signature file format

Each YAML file is a list of signature dicts:

```yaml
- regex: '(?i)(^|\.)bayern\.de$'
  software: "Government Mail Gateway (Freistaat Bayern)"
  vendor: "Freistaat Bayern"
  vendor_country: "DE"
  vendor_category: "Community / Public Sector / Gemeinwohl"
  role: "smtp_in"
  open_source_rating: 6
  vendor_country_rating: 1
  vendor_category_rating: 1
```

| File | matched against | typical contents |
|---|---|---|
| `mx.yaml` | MX hostnames | German federal/state government gateways, municipal data centres (KRZ, KDO, ekom21…), DE/EU hosters (IONOS, STRATO, Host Europe), security gateways (Hornetsecurity, Proofpoint, Mimecast, Barracuda), US hyperscalers (Google, `mail.protection.outlook.com`). Many are `role: proxy`. |
| `smtp.yaml` | SMTP banners | NoSpamProxy, Hornetsecurity, Postfix, Exim, MS Exchange, Proxmox, Barracuda. |
| `imap.yaml` | IMAP banner + host | Dovecot, Cyrus, Courier, MS 365/Exchange Online, Gmail, Zimbra, Kerio, GMX/mail.com, STRATO, mailbox.org. |

Each entry hard-codes its three ratings (`vendor_country_rating`,
`vendor_category_rating`, `open_source_rating`).

### 8.3 Linter — `parse_signature.py`

`ValidationRunner` checks every signature for consistency: `vendor_category_rating`
must equal `VendorCategory(category).rating`, `vendor_country_rating` must equal
`VendorCountryRating.from_country_code(country)`, and `role` must be a valid
`MailSystemRole`. It reports problems (auto-correct is disabled). The
`test_signatures.py` test suite enforces the same rules.

---

## 9. Step 3 — Persistence (`to_db.py` + `db/`)

### 9.1 The versioned schema (SCD-2)

The schema separates **entities** (deduplicated, stored once) from **history /
link tables** (one versioned row per scan run). Every row in a history table has:

- `valid_from_run` → the run that introduced this state,
- `valid_to_run` → the run that ended it (`NULL` while current),
- `is_current` → boolean flag for fast "current state" queries.

`history.update_history(session, model, run, match, tracked)` implements the
Slowly-Changing-Dimension-Type-2 logic: if the tracked values are unchanged it is
a no-op; if they changed, the current row is closed (`is_current=False`,
`valid_to_run=run.id`) and a fresh `is_current=True` row is inserted. This is how
the database keeps full history across runs.

#### Tables

**`scanner_runs`** — one row per scan run.

| column | type |
|---|---|
| `id` | UUID PK |
| `started_at` | timestamp |
| `finished_at` | timestamp |
| `scanner_version_git_hash` | text |

**`organisations`** — one row per organisation (entity).

| column | type |
|---|---|
| `id` | UUID PK |
| `name` | text |
| `wikidata_url` | text |
| `city`, `state`, `country` | text |
| `category_tag` | text |
| `longitude`, `latitude` | real |
| `website` | text |

**`mail_systems`** — one row per detected product (entity), **deduplicated by
`(software, role)`** and shared across organisations.

| column | type |
|---|---|
| `id` | UUID PK |
| `role` | enum (`smtp_out`/`smtp_in`/`imap_pop3`/`webmailer`/`proxy`) |
| `software` | text |
| `vendor`, `vendor_country`, `vendor_category` | text |
| `vendor_country_rating`, `open_source_rating`, `vendor_category_rating` | int |

`UniqueConstraint(software, role)`.

**`ip_addresses`** — one row per IP (entity).

| column | type |
|---|---|
| `id` | UUID PK |
| `ip_address` | text (unique) |
| `rdns_hostname` | text (from PTR) |
| `asn`, `asn_org`, `country_code` | int / text |
| `country_rating` | int (derived from country) |
| `asn_rating` | int (derived hoster rating) |

**`org_domain_history`** — org ↔ its domains.

| column | type |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `email_domain`, `website_domain` | text |
| `valid_from_run`, `valid_to_run`, `is_current` | versioning |

**`org_mail_system_history`** — org ↔ mail system, with optional in-front proxy.

| column | type |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `mail_system_id` | FK → mail_systems |
| `proxy_system_id` | FK → mail_systems (nullable) |
| `valid_from_run`, `valid_to_run`, `is_current` | versioning |

**`mail_system_ip_history`** — org ↔ mail system ↔ IP. The link carries
`organisation_id` so a shared mail system keeps **per-organisation** geography.

| column | type |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `mail_system_id` | FK → mail_systems |
| `ip_address_id` | FK → ip_addresses |
| `valid_from_run`, `valid_to_run`, `is_current` | versioning |

> `base.py::migrate_legacy_schema` exists exactly because of the last point: an
> older global-pool `mail_system_ip_history` (without `organisation_id`) is
> dropped and rebuilt org-scoped; the data is repopulated on the next scan.

### 9.2 Rating derivation — `db/models.py`

Two derivations turn raw IP facts into ratings:

- **`VendorCountryRating.from_country_code(code)`** →
  `DE`=1; EU/EEA/CH set=2; `US`=5; `{RU,CN,IR,KP}`=6; everything else=3. Populates
  `ip_addresses.country_rating` (and validates vendor-country ratings).
- **`derive_hoster_rating(country_code, asn_org)`** → if `asn_org` contains a
  hyperscaler keyword (GOOGLE, AMAZON/AWS, MICROSOFT/AZURE, ORACLE, CLOUDFLARE,
  AKAMAI, FASTLY, DIGITALOCEAN, LINODE) → **5**; otherwise a country base
  (DE/EU=2, adequacy third country=4, US=5, high-risk=6). Populates
  `ip_addresses.asn_rating`.

`VendorCategory` maps the category string to a rating: Community/Public Sector=1,
EU Software Vendor=2, EU Subsidiary of Foreign Vendor=3, International Vendor=4,
US Hyperscaler=5, Unknown/Sanctioned=6.

### 9.3 What `to_db.py` writes

`to_db(session, run, registry)` runs in this order:

1. `_build_org_domain` — bridge org → scanned domains.
2. `_build_detections` — run `match_signature` over SMTP banners + MX hostnames
   (`mx_detections`) and IMAP banner + host (`domain_detections`).
3. `_sync_ip_addresses` — `get_or_create(IpAddress)` per IP, set `country_rating`
   and `asn_rating`.
4. `_sync_mail_systems` — `get_or_create(MailSystem)` per `(software, role)`, set
   vendor/ratings.
5. `_sync_org_mail_system_history` — link orgs to mail systems. **Proxy pairing
   rule:** within one `(org, mx_domain)` group, a detected proxy is attached to
   each detected server via `proxy_system_id`; a lone proxy is linked on its own.
6. `_sync_mail_system_ip_history` — link each org's MX IPs to its mail systems.
7. `_sync_fallback_mail_systems` — orgs that have a resolvable MX but **no**
   signature match are linked to a shared `Unidentified Mail Server` (`smtp_in`)
   plus their MX IPs, so they can still be scored on IP geography alone.

---

## 10. Step 4 — The sovereignty index (`sovereignty_index_calc.py`)

Scale: **1 = very sovereign … 6 = not sovereign.** The index is computed in three
stages so that one foreign sub-system (e.g. a US inbound filter) cannot be averaged
away. The full specification lives in
[`Souveränitätsindex_V2_Spezifikation.md`](../../Souveränitätsindex_V2_Spezifikation.md);
the implemented algorithm is:

### Stage 1 — per-system score `_system_score(system)`

Weighted mean of up to five markers:

| Marker | Source | Weight |
|---|---|---|
| IP country | mean of `ips[].country_rating` | 15 |
| IP hoster | mean of `ips[].hoster_rating` | 15 |
| Vendor category | `vendor_category_rating` | 10 |
| Vendor country | `vendor_country_rating` | 10 |
| Open source | `open_source_rating` | 10 |

Missing markers are **dropped** and the remaining weights are re-normalised, so a
data gap produces neither an artificially good nor bad grade. Returns
`(score, n_markers_present)`.

### Stage 2 — role score `_role_score(systems)`

For each role (`imap_pop3`, `smtp_in`, `smtp_out`, `webmailer`):

- **Proxy max-rule:** if a proxy sits in front, `score = max(system, proxy)` — a
  path is only as sovereign as its weakest (highest-numbered) link, because mail
  passes through the proxy in clear text.
- Multiple systems of the same role are averaged.
- It also counts missing markers (`nb_count += 5 − n_markers`) for the
  data-quality brake.

### Stage 3 — org final score `compute_sovereignty_index(mail_systems)`

```
role weights:  imap_pop3 0.30 · smtp_in 0.25 · smtp_out 0.25 · webmailer 0.20

mean   = Σ(role_score · weight) / Σ(weight)      # over the roles that exist
worst  = max(role_score)
final  = 0.60 · mean + 0.40 · worst
grade  = round_half_up(final)                    # integer 1..6
```

**Data-quality brake:** if, averaged over the rated roles, more than 3 of the 5
per-system markers are missing (`nb_total > 3 × number_of_rated_roles`), **no
grade is produced** and the org is reported as *n.b.* (`sovereignty_index = null`).
This is why an IP-only fallback (`Unidentified Mail Server`, 2 markers / 3 missing)
is exactly at the threshold and still rated, while a single-marker org is
suppressed.

`compute_average_index(orgs)` returns the mean of all non-null grades (used for the
overview file).

---

## 11. Step 5 — JSON export (`dump.py`)

`write_dump(session)` serialises every organisation and writes two outputs into
`database/export/`:

1. **`organizations.json`** — the full per-org array consumed by the frontend.
2. **`<YYYY-MM-DD>.json`** — an aggregate overview snapshot.

Both are also written Brotli-compressed (`.json.br`).

### 11.1 Per-org document

`_serialize_org` emits exactly these keys:

```jsonc
{
  "org": "Stadt Mannheim",
  "domain": "mannheim.de",            // website_domain, else email_domain
  "email_domain": "mannheim.de",
  "category": "city",
  "wikidata_url": "http://www.wikidata.org/entity/Q2119",
  "city": "Mannheim", "state": "Baden-Württemberg", "country": "Deutschland",
  "lat": 49.48, "long": 8.46,
  "last_checked": "2026-06-26T15:42:00Z",   // newest run timestamp
  "sovereignty_index": 5,                    // 1..6 or null
  "providers": ["Microsoft"],                // distinct vendors
  "hosters": ["MICROSOFT-CORP-MSN-AS-BLOCK"],// distinct ASN orgs
  "mail_systems": {
    "smtp_in":  [ { /* MailSystem */ } ],
    "smtp_out": [ ... ],
    "imap_pop3":[ ... ],
    "webmailer":[ ... ]
  }
}
```

Each `MailSystem` is **slimmed** (`_slim_system`): raw per-IP detail is dropped and
replaced by distinct `countries` (ISO-2 codes) and `hosters` (ASN orgs). The
`proxy` field is a recursively slimmed mail system (or `null`); proxy depth is
capped at one level. Export roles are `smtp_out / smtp_in / imap_pop3 / webmailer`;
a standalone `proxy` detection is folded into `smtp_in`. The
`sovereignty_index` is computed from the **full** (un-slimmed) structure before
slimming.

### 11.2 Overview document

`_build_overview` produces:

```jsonc
{
  "overview": {
    "orgsScanned": 5025,
    "domainsScanned": 173,          // unique email_domains
    "sovereigntyIndex": 2.33        // average of non-null grades
  },
  "topMailVendors": [ { "name": "Microsoft", "share": 0.41 }, ... ],  // top 10
  "topHosters":     [ { "name": "...",       "share": 0.22 }, ... ]
}
```

`share = round(count / total, 2)`.

---

## 12. Testing (`tests/`)

Pure unit tests, no DB/network:

- **`test_sovereignty_index_calc.py`** — pins the weighted mean, per-system IP
  averaging, the proxy max-rule, multi-role aggregation, half-up rounding, the
  data-quality brake, and the IP-only fallback (DE host → 2, US → 5, 3 missing
  still rated, 4 missing → `null`).
- **`test_dump.py`** — `_serialize_ip` field renames (`asn_org`→`hoster`,
  `asn_rating`→`hoster_rating`), `_top_shares`, `_build_overview`.
- **`test_signatures.py`** — every signature's ratings are self-consistent, no
  `software` label maps to two vendors, ~20 real government/provider MX hosts
  resolve correctly, and anchored rules don't fire on look-alikes
  (`oberbayern.de`, `verbund.de`).
- **`test_org_list_pipeline.py`** / **`test_email_scraper.py`** — the
  normalisation helpers.

Run with `cd scanner && uv run pytest`.

---

## 13. Known gaps, stale artifacts & caveats

These are documented honestly so future maintainers aren't surprised:

- **Two scanning code paths exist.** The canonical one is `scanner_pipeline/`
  (used by `main.py`). `enricher/` is an older "bronze" prototype with hard-coded
  `/home/julian/…` paths reading a separate `raw_data.db`; it is **not** wired into
  `main.py`.
- **`scanner/README.md` is stale** — it says the DB is `domainlist.db`; the actual
  file is `SMART.db`.
- **`SPF` is scanned but never persisted** by `to_db.py`.
- **`config.yml`** (in `src/`) is a separate, apparently unused rating config — the
  live ratings come from the signature YAMLs and `db/models.py`.
- **`extract.py`** in the signatures pipeline is an empty stub.
- **`tldextract`** is imported but not declared in `pyproject.toml`.
- **`scanner/docs/db/db.puml`** (ER diagram) omits `mail_system_ip_history.organisation_id`.
- Per the V2 spec's open TODOs: `vendor_category_rating` should be re-mapped so
  community/public-sector vendors like DFN grade 1 (not 2), and the open-source
  scale currently only uses 1 and 6 in real data.
