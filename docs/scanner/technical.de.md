# S.M.A.R.T. Scanner — Technische Dokumentation (DE)

> **S.M.A.R.T.** = **S**overeign **M**ail **A**ssessment and **R**ating **T**ool.
> Der Scanner ermittelt die Mail-Infrastruktur öffentlicher Organisationen im
> DACH-Raum (Deutschland, Österreich, Schweiz), erkennt die eingesetzten Produkte
> und Hersteller, leitet je Organisation eine Souveränitätsnote ab und exportiert
> das Ergebnis als JSON für das Frontend.

Dieses Dokument beschreibt den Scanner so, wie er **tatsächlich implementiert**
ist. Die nicht-technische Bedienungsanleitung steht in [user.de.md](user.de.md),
die englische Fassung in [technical.en.md](technical.en.md).

---

## 1. Was der Scanner leistet

Für jede bekannte Organisation beantwortet der Scanner die Frage:

> *Wird die E-Mail dieser Organisation auf souveräner (EU-/öffentlicher/offener)
> Infrastruktur betrieben — oder hängt sie von ausländischen Hyperscalern wie
> Microsoft 365 oder Google Workspace ab?*

Dazu:

1. baut er aus **Wikidata** eine Liste von Organisationen und ihren Domains auf;
2. löst er je Domain die **MX-/IP-/ASN-/PTR-/SMTP-/IMAP**-Einträge auf;
3. erkennt er per **Regex-Signaturen** die Mailprodukte und Hersteller
   (*Fingerprinting*);
4. speichert er alles in einem **versionierten SQLite-Schema** (eine Zeile je
   Scan-Lauf);
5. berechnet er den **Souveränitätsindex V2** (Note 1–6);
6. **exportiert** er ein schlankes JSON-Dokument plus eine aggregierte Übersicht.

Die Skala ist eine Schulnoten-Skala: **1 = sehr souverän … 6 = nicht souverän**,
`null` = nicht bewertbar.

---

## 2. Datenfluss von Anfang bis Ende

```
                 ┌─────────────────────────────────────────────────────────┐
                 │  Wikidata (QLever SPARQL)                               │
                 └───────────────────────────┬─────────────────────────────┘
                                             │  Organisationen + Domains
                                             ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  SQLite:  organisations · org_domain_history                     │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  aktuelle Domains
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Scan-Pipeline (async):  MX → IP → ASN → PTR / SMTP / IMAP / SPF │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  Rohbeobachtungen (pandas)
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Signatur-Matcher:  MX-Host / SMTP-Banner / IMAP-Banner → Vendor │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  Detections
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  to_db:  mail_systems · ip_addresses · *_history-Linktabellen    │
        └───────────────────────────┬──────────────────────────────────────┘
                                     │  bewertete Struktur
                                     ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  Souveränitätsindex-Berechnung  +  JSON-Export (+ Brotli)        │
        └───────────────────────────┬──────────────────────────────────────┘
                                     ▼
              database/export/organizations.json   (Detail je Org)
              database/export/<YYYY-MM-DD>.json     (Aggregat-Übersicht)
```

`main.py` führt die komplette Kette **Org-Zustand versionieren → scan → to_db →
dump** aus. Schritt 0 ist **kein** Neuaufbau der Liste von Grund auf: Er schreibt
den aktuellen Wikidata-Org-/Domain-Zustand als neue SCD-2-History-Version des Laufs
fort, sodass Domain-Änderungen zwischen den Läufen über die Zeit erfasst werden.
Anschließend werden die resultierenden aktuellen Domains gescannt.

---

## 3. Technologie & Voraussetzungen

| Aspekt | Wahl |
|---|---|
| Sprache | Python **3.12+** (`.python-version` = `3.12`) |
| Paket-/venv-Manager | **uv** (`uv sync`, `uv run`) |
| Datenbank | **SQLite** über **SQLAlchemy 2.0** ORM (declarative) |
| Async-I/O | `asyncio`, `aiodns`, `dnspython` |
| Web-Scraping | **Scrapy** (E-Mail-Scraper), `requests` (SPARQL) |
| Datenaufbereitung | **pandas** |
| Kompression | **Brotli** (Export `.json.br`) |
| Tests | **pytest** (+ `pytest-cov`) |

Wichtige Laufzeit-Abhängigkeiten (`pyproject.toml`): `aiodns`, `brotli`,
`dnspython`, `ipwhois`, `overpy`, `pandas`, `pyyaml`, `requests`, `scrapy`,
`sqlalchemy`. Dev-Gruppe: `pytest`, `pytest-cov`.

> **Hinweis:** `tldextract` wird von der Domain-Listen-Pipeline importiert, ist
> aber **nicht** in `pyproject.toml` deklariert (aktuell transitiv aufgelöst). Bei
> Verschärfung des Lockfiles explizit ergänzen.

---

## 4. Projektaufbau

```
scanner/
├── main.py                       # Einstieg: Org-Zustand versionieren → scan → to_db → dump
├── pyproject.toml / uv.lock      # Abhängigkeiten, gelockt
├── database/
│   ├── SMART.db                  # die Arbeitsdatenbank
│   └── export/                   # JSON- + Brotli-Ausgabe
└── src/
    ├── config.yml                # Legacy-Rating-Konfig (zur Laufzeit UNGENUTZT)
    ├── db/
    │   ├── base.py               # Engine/Session, create_all, Legacy-Migration
    │   ├── models.py             # ORM-Tabellen + Rating-Enums/-Helfer
    │   ├── runs.py               # ScannerRun-Context-Manager, Git-Hash
    │   └── history.py            # SCD-2-Versionierung (update_history)
    ├── domainlist_pipline/
    │   ├── config.yaml           # Wikidata: Institutionen × Gebiete (GENUTZT)
    │   ├── org_list_pipeline.py  # Wikidata/QLever-Abruf + Persistenz
    │   └── email_scraper.py      # Scrapy-Crawl für fehlende E-Mail-Domains
    ├── scanner_pipeline/
    │   ├── step.py               # abstrakter async Step (eine Beobachtungsart)
    │   ├── registry.py           # abhängigkeitsgeordneter Step-Runner
    │   ├── asn_bulk.py           # Team-Cymru-Bulk-ASN/whois-Lookups
    │   └── to_db.py              # schreibt Entitäten + History-Linktabellen
    ├── signatures_pipeline/
    │   ├── matcher.py            # load_signatures / match_signature
    │   ├── parse_signature.py    # Signatur-Linter/-Validator
    │   └── signatures/
    │       ├── mx.yaml           # gegen MX-Hostnamen
    │       ├── smtp.yaml         # gegen SMTP-Banner
    │       └── imap.yaml         # gegen IMAP-Banner + Host
    └── json_dumper/
        ├── dump.py               # serialisiert Orgs → JSON, baut Übersicht
        └── sovereignty_index_calc.py   # der Bewertungsalgorithmus
```

---

## 5. Der Einstieg — `main.py`

`main.py` orchestriert genau einen Scan-Lauf. Es gibt kein Argument-Parsing; die
einzigen Stellschrauben sind zwei Modul-Konstanten:

```python
DB_NAME = "SMART.db"
SAMPLE_LIMIT: int | None = None   # Integer = nur N Domains scannen (zum Testen)
```

`main(db_path=None, sample_limit=SAMPLE_LIMIT)` macht:

1. DB-Pfad auflösen (Default `scanner/database/SMART.db`).
2. `make_engine` → `create_all` → `make_session`.
3. `scanner_run(session)`-Kontext öffnen (legt eine `ScannerRun`-Zeile an, gibt
   `run.id` aus).
4. **Org-Zustand versionieren** — `wikidata_fetch_and_persist(session, run, WIKIDATA_CONFIG)`
   schreibt den aktuellen Wikidata-Org-/Domain-Zustand als neue SCD-2-History-Version
   des Laufs fort (kein Neuaufbau von Grund auf); `update_history` öffnet nur dann
   eine neue Zeile, wenn sich eine getrackte Domain wirklich geändert hat — so werden
   Domain-Änderungen über die Zeit erfasst. Danach `session.commit()`, damit die
   frischen Orgs für den nächsten Schritt sichtbar sind (der über eine eigene
   unabhängige `sqlite3`-Verbindung liest).
5. **Scan** — `Registry.from_sqlite(db_path, _domain_query(sample_limit))`, dann
   `asyncio.run(registry.run_queue())`.
6. **Persistenz** — `to_db(session, run, registry)`.
7. **Export** — `count = write_dump(session)`; gibt die Org-Anzahl aus.

`_domain_query()` wählt die zu scannenden Domains:

```sql
SELECT * FROM org_domain_history
WHERE is_current = 1
  AND (website_domain IS NOT NULL OR email_domain IS NOT NULL)
[ LIMIT N ]
```

Start mit `cd scanner && uv run main.py`.

---

## 6. Schritt 0 — Aufbau der Organisations-/Domain-Liste

Diese Stufe pflegt `organisations` und `org_domain_history`. `main.py` führt sie bei
jedem Lauf zuerst über `wikidata_fetch_and_persist` aus, noch vor dem Scan. Sie baut
die Liste **nicht** von Grund auf neu: Jeder Lauf schreibt den aktuellen
Wikidata-Org-/Domain-Zustand als neue SCD-2-History-Version fort (siehe §9.1), sodass
die **zeitliche** Dimension — wann sich die Domains einer Organisation ändern — Lauf
für Lauf erfasst wird.

### 6.1 Wikidata-Abruf — `org_list_pipeline.py`

- Fragt den **QLever**-Wikidata-Endpunkt (`https://qlever.dev/api/wikidata`) per
  SPARQL ab, User-Agent `SMART-BOT/1.4`, mit bis zu `MAX_ATTEMPTS = 3` Versuchen.
- Welche Entitäten abgerufen werden, steuert `domainlist_pipline/config.yaml`:

  ```yaml
  institutions:                 # Wikidata-QIDs + zusätzliche SPARQL-Filter
    university:      { qid: Q3918 }
    hospital:        { qid: Q16917 }
    school:          { qid: Q132050, filters: [ "FILTER NOT EXISTS { ?item wdt:P31/wdt:P279* wd:Q3918. }" ] }
    courthouse:      { qid: Q41487 }
    city:            { qid: Q515 }
    political party: { qid: Q7278, filters: [ "?item wdt:P31 wd:Q7278." ] }
    newspaper:       { qid: Q11032 }
  areas:                        # abzudeckende Länder
    germany: Q183
    austria: Q40
    switzerland: Q39
  ```

  Die Pipeline ruft das **Kreuzprodukt** Institution × Gebiet ab. Ausgewählte
  Properties: Label, Website (`P856`), E-Mail (`P968`), Koordinaten (`P625`),
  Stadt / Bundesland / Land (deutsche Labels).

  Wie die Config auf die SPARQL-Query abbildet:

  - **`institutions`** — jeder Eintrag ist ein abzurufender Organisationstyp. Der
    **Schlüssel** (z. B. `university`) wird als `category_tag` der Organisation
    gespeichert.
    - **`qid`** — die Basisquery matcht jedes Item, das *Instanz von oder
      Unterklasse von* diesem QID ist (`?item wdt:P31/wdt:P279* wd:<qid>`).
    - **`filters`** — optionale zusätzliche SPARQL-Zeilen, die in den `WHERE`-Block
      eingefügt werden (ersetzen den Platzhalter `{EXTRA_FILTERS}`), um Ergebnisse
      einzuschränken oder auszuschließen. `school` schließt alles aus, das zugleich
      Universität ist, damit Unis nicht doppelt erscheinen; `political party`
      beschränkt auf eine *direkte* Instanz von `Q7278`
      (`?item wdt:P31 wd:Q7278.`) statt auch Unterklassen zu ziehen; ein leeres
      `filters: []` fügt keine Einschränkung über die Basisquery hinaus hinzu.
  - **`areas`** — bildet einen Ländernamen auf seine Wikidata-QID ab; die Basisquery
    filtert auf `?item wdt:P17 wd:<qid>` (Land des Items), sodass nur Organisationen
    in diesem Land zurückkommen.

  Um einen neuen Organisationstyp oder ein neues Land zu ergänzen, genügt ein
  weiterer Eintrag — keine Code-Änderung nötig.

- Normalisierungs-Helfer:
  - `extract_website_domain()` → registrierte Domain via `tldextract`
    (`www.mannheim.de`, `en.mannheim.de` → `mannheim.de`).
  - `normalize_email_to_domain()` → kleingeschriebene Domain nach dem `@`.
- Persistenz (`_persist_record`): `get_or_create(Organisation, wikidata_url=…)`,
  Skalarfelder aktualisieren, dann `update_history(OrgDomainHistory, …)` mit den
  getrackten Feldern `email_domain` und `website_domain`. Eine vorhandene
  E-Mail-Domain bleibt erhalten, wenn Wikidata keine liefert.

### 6.2 E-Mail-Scraper — `email_scraper.py`

> **Aktuell nicht in `main.py` eingebunden.** `run_scraper` existiert, wird aber
> während eines Laufs von nichts aufgerufen; nur die Helfer sind unit-getestet. Die
> offene Integrationsfrage steht in §13.

Wenn ausgeführt, füllt er `email_domain` für aktuelle Orgs, die noch keine haben,
mit einem **Scrapy**-Spider (`mailto_spider`):

- Einstellungen: `DOWNLOAD_TIMEOUT=12`, `ROBOTSTXT_OBEY=True`,
  `CONCURRENT_REQUESTS=16`, `CONCURRENT_REQUESTS_PER_DOMAIN=2`,
  `DOWNLOAD_DELAY=0.5`, UA `SMART-BOT/1.4`.
- Hat die Org bereits ein `smtp_in`-Mailsystem, wird `email_domain` direkt auf die
  `website_domain` gesetzt (kein Crawl).
- Sonst wird die Startseite nach `mailto:`-Adressen durchsucht; werden keine
  gefunden, wird einmalig dem ersten *Impressum*/*Kontakt*-Link gefolgt.
- Generische Local-Parts (`noreply`, `webmaster`, `postmaster`, …) werden bei der
  Domain-Wahl ignoriert.

---

## 7. Schritt 1 — Die Scan-Pipeline (`scanner_pipeline/`)

Die Scan-Pipeline ist ein **asynchroner, abhängigkeitsgeordneter DAG** über
pandas-DataFrames.

### 7.1 Was ein „Step“ ist — `step.py`

`Step` ist eine abstrakte Basisklasse. Jeder konkrete Step konsumiert eine Spalte
aus der Ausgabe seines `required_step` und erzeugt neue Zeilen.

- `input_col` — die gelesene Spalte.
- `required_step` — der Step, dessen Ausgabe konsumiert wird.
- `async get(value) -> list[dict]` — die Arbeit je Wert (eine DNS-/TCP-Probe usw.).
- Die Nebenläufigkeit ist durch ein `asyncio.Semaphore` (Default 20) begrenzt.
- `_run_task` umschließt `get` mit try/except und hängt ein `error`-Feld an
  (`None` bei Erfolg, sonst der Exception-Text).
- `scan(data)` = `preprocess` (dropna + Dedupe auf `input_col`) → `get_func`
  (Fan-out + Fortschrittsanzeige + Flatten) → `postprocess` (Dedupe).

### 7.2 Die Steps und ihre Abhängigkeiten

| Step | benötigt | Eingabespalte | Ausgabespalten | Probe |
|---|---|---|---|---|
| `Domain` | — (Seed) | — | `organisation_id, website_domain, email_domain` | DB-Zeilen |
| `Combiner` | `Domain` | — | `organisation_id, domain` | website + email → `domain` |
| `MX` | `Combiner` | `domain` | `domain, mx_domain` | DNS MX |
| `IP` | `MX` | `mx_domain` | `mx_domain, ip` | `getaddrinfo` |
| `ASN` | `IP` | `ip` | `ip, asn, owner, country, error` | Team-Cymru-Bulk-WHOIS |
| `PTR` | `IP` | `ip` | `ip, ptr` | Reverse DNS |
| `SMTP` | `MX` | `mx_domain` | `mx_domain, smtp_banner, port` | Verbindung 25/587/465, Banner |
| `IMAP` | `Combiner` | `domain` | `domain, imap_host, port, banner` | Hosts `imap/mail/webmail/exchange` × Ports 143/993 |
| `SPF` | `Combiner` | `domain` | `domain, spf` | TXT-Records `v=spf1…` |

> `SPF` wird erhoben, von `to_db.py` aber **nicht** persistiert (siehe §13).

### 7.3 Die Registry — `registry.py`

`Registry` hält eine `queue` von Step-Instanzen und ein `results`-Dict
`StepClass → DataFrame`.

- `run_queue()` wählt wiederholt den ersten Step, dessen `required_step`-Ausgabe
  schon vorliegt, führt ihn aus, speichert das Ergebnis und entfernt ihn — die
  Queue **ordnet sich also selbst nach Abhängigkeiten**.
- `from_sqlite(db, query)` befüllt das `Domain`-Ergebnis aus der DB-Abfrage und
  reiht die übrigen Steps ein.

### 7.4 Bulk-ASN-Lookup — `asn_bulk.py`

- `lookup_asn_bulk(ips)` spricht **Team Cymru** Bulk-WHOIS
  (`whois.cymru.com:43`) in Batches zu 1000 an, parst die pipe-getrennte Antwort
  und liefert `{ip: {asn, asn_org, country_code}}`. Socket-Fehler werden
  abgefangen (der Batch wird übersprungen).
- `enrich_ip_addresses(session, only_missing=True)` ist ein **Recovery-Werkzeug**:
  führt das ASN-Lookup für `ip_addresses`-Zeilen erneut aus (optional nur die ohne
  `asn_org`), aktualisiert `asn`, `asn_org`, `country_code` sowie die abgeleiteten
  `country_rating`/`asn_rating` und committet. Nach einem durch DNS-Rate-Limits
  beeinträchtigten Scan einsetzen, danach `write_dump` erneut laufen lassen.

---

## 8. Schritt 2 — Signatur-Matching (`signatures_pipeline/`)

Hersteller-/Produkterkennung über Regex-Signaturen.

### 8.1 Der Matcher — `matcher.py`

- `SIGNATURE_FIELDS` sind die 8 Felder, die ein Treffer zu einem Mailsystem
  beiträgt: `software, role, vendor, vendor_country, vendor_category,
  vendor_country_rating, open_source_rating, vendor_category_rating`.
- `load_signatures(kind)` (LRU-gecacht) liest `signatures/<kind>.yaml` und
  kompiliert das `regex` jedes Eintrags.
- `match_signature(kind, *texts)` liefert die **erste** Signatur, deren Muster auf
  einen der Texte passt (**Dateireihenfolge zählt**), oder `None`.

### 8.2 Format der Signaturdateien

Jede YAML-Datei ist eine Liste von Signatur-Dicts:

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

| Datei | abgeglichen mit | typischer Inhalt |
|---|---|---|
| `mx.yaml` | MX-Hostnamen | Bundes-/Landes-Behördengateways, kommunale Rechenzentren (KRZ, KDO, ekom21…), DE/EU-Hoster (IONOS, STRATO, Host Europe), Security-Gateways (Hornetsecurity, Proofpoint, Mimecast, Barracuda), US-Hyperscaler (Google, `mail.protection.outlook.com`). Viele mit `role: proxy`. |
| `smtp.yaml` | SMTP-Banner | NoSpamProxy, Hornetsecurity, Postfix, Exim, MS Exchange, Proxmox, Barracuda. |
| `imap.yaml` | IMAP-Banner + Host | Dovecot, Cyrus, Courier, MS 365/Exchange Online, Gmail, Zimbra, Kerio, GMX/mail.com, STRATO, mailbox.org. |

Jeder Eintrag kodiert seine drei Ratings fest (`vendor_country_rating`,
`vendor_category_rating`, `open_source_rating`).

### 8.3 Linter — `parse_signature.py`

`ValidationRunner` prüft jede Signatur auf Konsistenz: `vendor_category_rating`
muss `VendorCategory(category).rating` entsprechen, `vendor_country_rating` muss
`VendorCountryRating.from_country_code(country)` entsprechen und `role` muss eine
gültige `MailSystemRole` sein. Probleme werden gemeldet (Auto-Korrektur ist
deaktiviert). Die Test-Suite `test_signatures.py` erzwingt dieselben Regeln.

---

## 9. Schritt 3 — Persistenz (`to_db.py` + `db/`)

### 9.1 Das versionierte Schema (SCD-2)

Das Schema trennt **Entitäten** (dedupliziert, einmal gespeichert) von **History-/
Linktabellen** (eine versionierte Zeile je Scan-Lauf). Jede History-Zeile hat:

- `valid_from_run` → der Lauf, der diesen Zustand einführte,
- `valid_to_run` → der Lauf, der ihn beendete (`NULL`, solange aktuell),
- `is_current` → Boolean-Flag für schnelle „aktueller Zustand“-Abfragen.

`history.update_history(session, model, run, match, tracked)` implementiert die
Slowly-Changing-Dimension-Type-2-Logik: sind die getrackten Werte unverändert,
passiert nichts; haben sie sich geändert, wird die aktuelle Zeile geschlossen
(`is_current=False`, `valid_to_run=run.id`) und eine neue `is_current=True`-Zeile
eingefügt. So hält die Datenbank die volle Historie über alle Läufe.

#### Tabellen

**`scanner_runs`** — eine Zeile je Scan-Lauf.

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `started_at` | Timestamp |
| `finished_at` | Timestamp |
| `scanner_version_git_hash` | Text |

**`organisations`** — eine Zeile je Organisation (Entität).

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `name` | Text |
| `wikidata_url` | Text |
| `city`, `state`, `country` | Text |
| `category_tag` | Text |
| `longitude`, `latitude` | Real |
| `website` | Text |

**`mail_systems`** — eine Zeile je erkanntem Produkt (Entität), **dedupliziert
nach `(software, role)`** und über Organisationen hinweg geteilt.

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `role` | Enum (`smtp_out`/`smtp_in`/`imap_pop3`/`webmailer`/`proxy`) |
| `software` | Text |
| `vendor`, `vendor_country`, `vendor_category` | Text |
| `vendor_country_rating`, `open_source_rating`, `vendor_category_rating` | Int |

`UniqueConstraint(software, role)`.

**`ip_addresses`** — eine Zeile je IP (Entität).

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `ip_address` | Text (unique) |
| `rdns_hostname` | Text (aus PTR) |
| `asn`, `asn_org`, `country_code` | Int / Text |
| `country_rating` | Int (aus Land abgeleitet) |
| `asn_rating` | Int (abgeleitete Hoster-Note) |

**`org_domain_history`** — Org ↔ ihre Domains.

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `email_domain`, `website_domain` | Text |
| `valid_from_run`, `valid_to_run`, `is_current` | Versionierung |

**`org_mail_system_history`** — Org ↔ Mailsystem, mit optionalem vorgeschaltetem
Proxy.

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `mail_system_id` | FK → mail_systems |
| `proxy_system_id` | FK → mail_systems (nullable) |
| `valid_from_run`, `valid_to_run`, `is_current` | Versionierung |

**`mail_system_ip_history`** — Org ↔ Mailsystem ↔ IP. Der Link trägt
`organisation_id`, damit ein geteiltes Mailsystem die **organisationsspezifische**
Geografie behält.

| Spalte | Typ |
|---|---|
| `id` | UUID PK |
| `organisation_id` | FK → organisations |
| `mail_system_id` | FK → mail_systems |
| `ip_address_id` | FK → ip_addresses |
| `valid_from_run`, `valid_to_run`, `is_current` | Versionierung |

> Die Datenbank liegt außerhalb der Versionsverwaltung (`scanner/database/` ist
> gitignored) und wird lokal neu aufgebaut, d. h. das Schema wird stets frisch von
> `create_all` erzeugt; es gibt keine In-place-Spaltenmigration. Wer noch eine alte
> lokale `SMART.db` von vor der `organisation_id`-Spalte hat, löscht sie und scannt
> neu.

### 9.2 Ableitung der Ratings — `db/models.py`

Zwei Ableitungen machen aus IP-Rohdaten Ratings:

- **`VendorCountryRating.from_country_code(code)`** →
  `DE`=1; EU/EWR/CH-Menge=2; `US`=5; `{RU,CN,IR,KP}`=6; alles andere=3. Befüllt
  `ip_addresses.country_rating` (und validiert die Vendor-Land-Ratings).
- **`derive_hoster_rating(country_code, asn_org)`** → enthält `asn_org` ein
  Hyperscaler-Stichwort (GOOGLE, AMAZON/AWS, MICROSOFT/AZURE, ORACLE, CLOUDFLARE,
  AKAMAI, FASTLY, DIGITALOCEAN, LINODE) → **5**; sonst eine Länderbasis
  (DE/EU=2, Drittland mit Angemessenheit=4, US=5, Hochrisiko=6). Befüllt
  `ip_addresses.asn_rating`.

`VendorCategory` bildet den Kategorie-String auf ein Rating ab:
Community/Public Sector=1, EU Software Vendor=2, EU-Tochter ausl. Vendor=3,
International Vendor=4, US-Hyperscaler=5, Unbekannt/Sanktioniert=6.

### 9.3 Was `to_db.py` schreibt

`to_db(session, run, registry)` läuft in dieser Reihenfolge:

1. `_build_org_domain` — Brücke Org → gescannte Domains.
2. `_build_detections` — `match_signature` über SMTP-Banner + MX-Hostnamen
   (`mx_detections`) und IMAP-Banner + Host (`domain_detections`).
3. `_sync_ip_addresses` — `get_or_create(IpAddress)` je IP, `country_rating` und
   `asn_rating` setzen.
4. `_sync_mail_systems` — `get_or_create(MailSystem)` je `(software, role)`,
   Vendor/Ratings setzen.
5. `_sync_org_mail_system_history` — Orgs mit Mailsystemen verknüpfen.
   **Proxy-Paarungsregel:** innerhalb einer `(org, mx_domain)`-Gruppe wird ein
   erkannter Proxy über `proxy_system_id` an jeden erkannten Server gehängt; ein
   alleinstehender Proxy wird für sich verlinkt.
6. `_sync_mail_system_ip_history` — die MX-IPs jeder Org mit ihren Mailsystemen
   verknüpfen.
7. `_sync_fallback_mail_systems` — Orgs mit auflösbarem MX, aber **ohne**
   Signaturtreffer, werden mit einem geteilten `Unidentified Mail Server`
   (`smtp_in`) plus ihren MX-IPs verknüpft. So bleiben Hoster und Land im Export
   sichtbar; da die Software unbekannt ist, fließt diese Komponente jedoch nicht
   in den Index ein (siehe Stufe 2).

---

## 10. Schritt 4 — Der Souveränitätsindex (`sovereignty_index_calc.py`)

Skala: **1 = sehr souverän … 6 = nicht souverän.** Der Index wird in drei Stufen
berechnet, damit ein einzelnes ausländisches Teilsystem (z. B. ein
US-Eingangsfilter) nicht weggemittelt wird. Die vollständige Spezifikation steht in
[`Souveränitätsindex_V2_Spezifikation.md`](../../Souveränitätsindex_V2_Spezifikation.md);
der implementierte Algorithmus:

### Stufe 1 — Per-System-Score `_system_score(system)`

Gewichteter Mittelwert von bis zu fünf Markern:

| Marker | Quelle | Gewicht |
|---|---|---|
| IP-Land | Mittel über `ips[].country_rating` | 15 |
| IP-Hoster | Mittel über `ips[].hoster_rating` | 15 |
| Vendor-Kategorie | `vendor_category_rating` | 10 |
| Vendor-Land | `vendor_country_rating` | 10 |
| Open-Source | `open_source_rating` | 10 |

Fehlende Marker werden **weggelassen** und die übrigen Gewichte renormiert — eine
Datenlücke erzeugt also weder eine künstlich gute noch schlechte Note. Rückgabe:
`(score, n_vorhandene_marker)`.

### Stufe 2 — Rollen-Score `_role_score(systems)`

Je Rolle (`imap_pop3`, `smtp_in`, `smtp_out`, `webmailer`):

- **Null-Komponente:** Systeme mit unidentifizierter Software (nur IP/Hoster
  bekannt, `software == "Unidentified Mail Server"`) werden komplett übersprungen
  — sie liefern keine Note und zählen auch nicht als fehlende Marker.
- **Proxy-max-Regel:** sitzt ein Proxy davor, gilt `score = max(System, Proxy)` —
  ein Pfad ist nur so souverän wie sein schwächstes (höchstes) Glied, da die Mail
  im Klartext durch den Proxy läuft.
- Mehrere Systeme derselben Rolle werden gemittelt.
- Fehlende Marker werden gezählt (`nb_count += 5 − n_marker`) für die
  Datenqualitäts-Bremse.

### Stufe 3 — Org-Endnote `compute_sovereignty_index(mail_systems)`

```
Rollengewichte:  imap_pop3 0,30 · smtp_in 0,25 · smtp_out 0,25 · webmailer 0,20

mean   = Σ(Rollen-Score · Gewicht) / Σ(Gewicht)   # über die vorhandenen Rollen
worst  = max(Rollen-Score)
final  = 0,60 · mean + 0,40 · worst
note   = kaufmännisch_runden(final)               # Ganzzahl 1..6
```

**Datenqualitäts-Bremse:** fehlen — gemittelt über die bewerteten Rollen — mehr
als 3 der 5 Per-System-Marker (`nb_total > 3 × Anzahl_bewertete_Rollen`), wird
**keine Note** vergeben und die Org als *n.b.* ausgewiesen
(`sovereignty_index = null`). Eine Org, deren einzige Komponente der IP-only-Fallback
(`Unidentified Mail Server`) ist, bleibt damit grundsätzlich unbewertet, der
Hoster wird zwar angezeigt, fließt aber nicht in eine Note ein.

`compute_average_index(orgs)` liefert das Mittel aller nicht-`null`-Noten (für die
Übersichtsdatei).

---

## 11. Schritt 5 — JSON-Export (`dump.py`)

`write_dump(session)` serialisiert jede Organisation und schreibt zwei Ausgaben
nach `database/export/`:

1. **`organizations.json`** — das vollständige Per-Org-Array für das Frontend.
2. **`<YYYY-MM-DD>.json`** — ein aggregierter Übersichts-Snapshot.

Beide werden zusätzlich Brotli-komprimiert (`.json.br`) geschrieben.

### 11.1 Per-Org-Dokument

`_serialize_org` gibt genau diese Schlüssel aus:

```jsonc
{
  "org": "Stadt Mannheim",
  "domain": "mannheim.de",            // website_domain, sonst email_domain
  "email_domain": "mannheim.de",
  "category": "city",
  "wikidata_url": "http://www.wikidata.org/entity/Q2119",
  "city": "Mannheim", "state": "Baden-Württemberg", "country": "Deutschland",
  "lat": 49.48, "long": 8.46,
  "last_checked": "2026-06-26T15:42:00Z",   // jüngster Lauf-Zeitstempel
  "sovereignty_index": 5,                    // 1..6 oder null
  "providers": ["Microsoft"],                // distinkte Vendors
  "hosters": ["MICROSOFT-CORP-MSN-AS-BLOCK"],// distinkte ASN-Orgs
  "mail_systems": {
    "smtp_in":  [ { /* MailSystem */ } ],
    "smtp_out": [ ... ],
    "imap_pop3":[ ... ],
    "webmailer":[ ... ]
  }
}
```

Jedes `MailSystem` wird **verschlankt** (`_slim_system`): die rohen Per-IP-Details
entfallen und werden durch distinkte `countries` (ISO-2) und `hosters` (ASN-Orgs)
ersetzt. Das Feld `proxy` ist ein rekursiv verschlanktes Mailsystem (oder `null`);
die Proxy-Tiefe ist auf eine Ebene begrenzt. Export-Rollen sind
`smtp_out / smtp_in / imap_pop3 / webmailer`; ein alleinstehender `proxy`-Treffer
wird zu `smtp_in` gefaltet. Der `sovereignty_index` wird aus der **vollen**
(unverschlankten) Struktur berechnet, bevor verschlankt wird.

### 11.2 Übersichts-Dokument

`_build_overview` erzeugt:

```jsonc
{
  "overview": {
    "orgsScanned": 5025,
    "domainsScanned": 173,          // distinkte email_domains
    "sovereigntyIndex": 2.33        // Mittel der nicht-null-Noten
  },
  "topMailVendors": [ { "name": "Microsoft", "share": 0.41 }, ... ],  // Top 10
  "topHosters":     [ { "name": "...",       "share": 0.22 }, ... ]
}
```

`share = round(count / total, 2)`.

---

## 12. Tests (`tests/`)

Reine Unit-Tests, ohne DB/Netzwerk:

- **`test_sovereignty_index_calc.py`** — fixiert gewichteten Mittelwert, Per-System-
  IP-Mittelung, die Proxy-max-Regel, Mehr-Rollen-Aggregation, kaufmännisches
  Runden, die Datenqualitäts-Bremse und den IP-only-Fallback (DE-Host → 2,
  US → 5, 3 fehlend noch bewertet, 4 fehlend → `null`).
- **`test_dump.py`** — `_serialize_ip`-Feldumbenennungen (`asn_org`→`hoster`,
  `asn_rating`→`hoster_rating`), `_top_shares`, `_build_overview`.
- **`test_signatures.py`** — alle Signatur-Ratings sind in sich konsistent, kein
  `software`-Label zeigt auf zwei Vendors, ~20 echte Behörden-/Provider-MX-Hosts
  werden korrekt aufgelöst, und verankerte Regeln feuern nicht auf Look-alikes
  (`oberbayern.de`, `verbund.de`).
- **`test_org_list_pipeline.py`** / **`test_email_scraper.py`** — die
  Normalisierungs-Helfer.

Start mit `cd scanner && uv run pytest`.

---

## 13. Bekannte Lücken, veraltete Artefakte & Hinweise

Ehrlich dokumentiert, damit künftige Betreuer nicht überrascht werden:

- **Der E-Mail-Scraper (`email_scraper.py::run_scraper`) ist noch nicht in den Lauf
  integriert.** Er ist implementiert, wird aber von `main.py` nie aufgerufen. Zu
  implementieren ist noch die **Abstimmung mit dem Scanner, *wann* E-Mails gescrapt
  werden müssen** — die Crawl-Entscheidung des Scrapers hängt von den Scan-Ergebnissen
  ab (er überspringt Orgs, die bereits ein `smtp_in`-Mailsystem haben, und crawlt nur
  die ohne auflösbaren MX), kann also nicht einfach als fester Schritt vor oder nach
  dem Scan laufen. Die Reihenfolge/der Trigger zwischen Scan und Scrape muss noch
  entworfen und eingebunden werden.
- **`SPF` wird gescannt, aber nie persistiert** (von `to_db.py`).
- **`extract.py`** in der Signatur-Pipeline ist ein leerer Stub.
- Laut den offenen TODOs der V2-Spezifikation sollte `vendor_category_rating` neu
  gemappt werden, sodass gemeinwohlorientierte Vendors wie DFN Note 1 (statt 2)
  erhalten; die Open-Source-Skala nutzt in echten Daten aktuell nur 1 und 6.
