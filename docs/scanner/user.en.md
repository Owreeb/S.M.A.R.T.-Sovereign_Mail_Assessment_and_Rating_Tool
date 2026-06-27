# S.M.A.R.T. Scanner — User Guide (EN)

This guide is for **operators** who want to run the scanner and understand its
output. It does not assume you know the internals — for those, see
[technical.en.md](technical.en.md). German version: [user.de.md](user.de.md).

---

## 1. What this tool is for

The S.M.A.R.T. scanner measures how **digitally sovereign** the e-mail of
public-sector organisations in Germany, Austria and Switzerland is. For each
organisation it determines which mail products and hosting providers are involved
and turns that into a single school grade:

| Grade | Meaning |
|---|---|
| **1** | very sovereign (own / EU / public-sector / open-source infrastructure) |
| **2** | sovereign |
| **3** | mixed |
| **4** | rather not sovereign |
| **5** | not sovereign (e.g. Microsoft 365 / Google Workspace) |
| **6** | not sovereign / high-risk or unknown |
| *n.b.* | not enough data to give a grade (`null` in the export) |

The results are written to JSON files that the frontend (the public website)
reads.

---

## 2. Prerequisites

You need:

1. **Python 3.12 or newer.**
2. **[uv](https://docs.astral.sh/uv/)** — the Python package/run manager used by
   this project.
3. An internet connection (the scanner makes DNS, SMTP, IMAP and WHOIS queries).

Check your versions:

```bash
python --version      # should be 3.12+
uv --version
```

---

## 3. Installation

From the repository root:

```bash
cd scanner
uv sync          # creates a virtual environment and installs all dependencies
```

That's it — `uv` reads `pyproject.toml`/`uv.lock` and sets everything up.

---

## 4. Running a scan

The main run refreshes the organisation list from Wikidata, scans every current
domain and produces the JSON export:

```bash
cd scanner
uv run main.py
```

What happens:

1. A new **scan run** is recorded (its ID is printed).
2. The **organisation/domain state is refreshed from Wikidata** and recorded as a
   new version in the history, so changes to an organisation's domains are tracked
   over time (universities, hospitals, schools, … for DE/AT/CH, configured in
   `config.yaml`).
3. Every organisation's domains are resolved (MX → IP → ASN → SMTP/IMAP/…).
4. Mail products and vendors are fingerprinted.
5. Results are stored in the database (with full history — old runs are kept).
6. The JSON export is written and the number of organisations is printed.

> **Note — internet & runtime.** Because step 2 queries Wikidata on every run, a
> full run also depends on the Wikidata endpoint being reachable.

> **Tip — test runs.** A full scan touches thousands of domains and takes a while.
> To try it on a small sample, open `scanner/main.py` and set
> `SAMPLE_LIMIT = 50` (or any number). Set it back to `None` for a full run.

### Where the database lives

The working database is `scanner/database/SMART.db`. It is created automatically on
the first run.

---

## 5. Understanding the output

After a successful run you'll find these files in `scanner/database/export/`:

| File | What it is |
|---|---|
| `organizations.json` | The full list — one entry per organisation, with its grade, providers, hosting countries and per-role mail systems. This is the file the frontend's map and table use. |
| `<YYYY-MM-DD>.json` | A dated **overview**: how many organisations were scanned, how many domains, the average grade, and the top mail vendors and hosters. The frontend uses two of these (newest + previous) to show "since last scan" trends. |
| `*.json.br` | Brotli-compressed copies of the above (smaller, same content). |

### What one organisation looks like

```jsonc
{
  "org": "Stadt Mannheim",
  "domain": "mannheim.de",
  "category": "city",
  "city": "Mannheim", "state": "Baden-Württemberg", "country": "Deutschland",
  "lat": 49.48, "long": 8.46,
  "last_checked": "2026-06-26T15:42:00Z",
  "sovereignty_index": 5,                 // the grade, 1..6, or null
  "providers": ["Microsoft"],             // software vendors detected
  "hosters": ["MICROSOFT-CORP-MSN-AS-BLOCK"],
  "mail_systems": { "smtp_in": [ … ], "smtp_out": [ … ], "imap_pop3": [ … ], "webmailer": [ … ] }
}
```

The four **mail-system roles** are:

- `smtp_in` — inbound mail (the MX server that receives mail).
- `smtp_out` — outbound mail.
- `imap_pop3` — the mailbox / client access.
- `webmailer` — browser-based webmail access.

Each role can have a **proxy** in front of it (e.g. a security filter like
Proofpoint). That matters for the grade: if a sovereign server sits behind a US
proxy, the inbound mail still passes through the US filter, so that path is graded
by the weaker (less sovereign) of the two.

---

## 6. How the grade is calculated (in plain terms)

For each mail system the scanner looks at up to five signals:

- which **country** the server IPs are in,
- who **hosts** those IPs (an EU operator? a US hyperscaler?),
- what **kind of vendor** makes the software (public-sector? EU company? US hyperscaler?),
- which **country** the software vendor is based in,
- whether the software is **open source** or proprietary.

These are combined into a per-system grade, the worst link of each role's path is
taken (proxy rule), and the four roles are weighted together — with extra weight on
the *worst* role so a single foreign system isn't hidden by averaging. The full
methodology is published in
[`Souveränitätsindex_V2_Spezifikation.md`](../../Souveränitätsindex_V2_Spezifikation.md)
and shown on the website's *Score Info* page.

If too much data is missing for an organisation, it is shown as **n.b.** (not
ratable) rather than getting a misleading grade.

---

## 7. Refreshing / re-running

- **Re-run a scan:** just run `uv run main.py` again. The database keeps the
  history of every run; the export always reflects the newest state.
- **Publish new data to the frontend:** copy the freshly written
  `organizations.json` and the dated `<YYYY-MM-DD>.json` from
  `scanner/database/export/` into `frontend/src/data/`, then rebuild the frontend.
  The frontend automatically uses the two newest dated files for its trend
  indicators.

---

## 8. The organisation list

The list of organisations comes from **Wikidata** and is **refreshed on every run**
as the first step of `main.py` — not rebuilt from scratch, but recorded as a new
version in the history so domain changes are tracked over time. It fetches
universities, hospitals, schools, courthouses, cities, political parties and
newspapers for Germany, Austria and Switzerland (configured in
`scanner/src/domainlist_pipline/config.yaml`).

To change *which* organisations are covered, edit `config.yaml` (add an
institution type or a country — no code changes needed) and run `uv run main.py`
as usual. A website crawler that fills in missing e-mail domains (`run_scraper`)
exists in the code but is **not run** at the moment — wiring it into the flow is
still an open task.

---

## 9. Troubleshooting

**Some organisations have no grade (`sovereignty_index: null`).**
This is expected and correct. It happens when the scanner couldn't gather enough
signals — often because DNS/SMTP/IMAP probes were rate-limited or timed out, or the
organisation has no resolvable mail server. The data-quality brake deliberately
withholds a grade rather than guessing.

**A whole scan looks under-populated (many missing ASN/hoster fields).**
A large scan can hit DNS or WHOIS rate limits. There is a recovery utility that
re-queries only the IP addresses that are missing their hosting info, fills them
in, and lets you re-export without re-scanning everything. Ask a developer to run
`enrich_ip_addresses(session)` followed by `write_dump(session)` (see the technical
docs, §7.4), then re-publish the export.

**The scan is slow.**
That's normal for a full run (thousands of domains, each with several network
probes). Use `SAMPLE_LIMIT` for quick tests.

**`uv: command not found`.**
Install uv first (see [uv installation](https://docs.astral.sh/uv/getting-started/installation/)),
then re-run `uv sync`.
