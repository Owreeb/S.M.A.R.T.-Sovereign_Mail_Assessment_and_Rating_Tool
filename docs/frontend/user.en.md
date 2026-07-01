# S.M.A.R.T. Frontend — User Guide (EN)

This guide explains how to **use the website**. No technical knowledge is required.
For the implementation, see [technical.en.md](technical.en.md). German version:
[user.de.md](user.de.md).

---

## 1. What the website shows

The S.M.A.R.T. website visualises how **digitally sovereign** the e-mail of
public-sector organisations in Germany, Austria and Switzerland is — i.e. whether
they run their mail on their own / EU / open infrastructure, or depend on foreign
providers such as Microsoft 365 or Google Workspace.

Every organisation gets a single **sovereignty grade from 1 to 6**:

| Grade | Colour | Meaning |
|---|---|---|
| **1** | green | very sovereign |
| **2** | light green | sovereign |
| **3** | yellow | mixed |
| **4** | orange | rather not sovereign |
| **5** | red | not sovereign |
| **6** | dark red | not sovereign / high-risk |
| — | grey | not enough data ("unknown") |

Lower is better. Organisations we couldn't grade are still shown (in grey) as long
as some mail infrastructure was found for them — they are only left out of the
grade-based statistics. Only organisations with no detectable mail system at all are
omitted.

---

## 2. The pages

The site has three pages, reachable from the top navigation bar:

- **Home (`/`)** — an introductory landing page explaining the project and the
  sovereignty idea, with a button to the dashboard.
- **Dashboard (`/dashboard`)** — the interactive data view: summary statistics, an
  insights section, the map, and the organisation table.
- **Score Info (`/score-info`)** — the full scoring methodology (how the 1–6 grade
  is computed).

You can switch the interface language between **DE** and **EN** with the toggle in
the navigation bar (German is the default). Your choice is remembered.

---

## 3. The dashboard

### 3.1 Overview statistics

At the top you'll find summary cards:

- **Organisations scanned** — how many organisations are in the current data.
- **Sovereignty index** — the average grade across all rated organisations (lower
  is better).
- **Domains scanned** — how many distinct e-mail domains were examined.

Each card shows a small **trend arrow** comparing the current scan to the previous
one ("since last scan"). For the sovereignty index, a *decrease* is shown as a good
(green) change, because a lower grade is better.

Below the cards, two **"top shares"** lists show the most common **mail vendors**
(e.g. Microsoft) and **hosting providers**, with their share of organisations.

### 3.2 Insights

The insights section shows three bar charts computed from the data:

1. **Score distribution** — how many organisations fall into each grade 1–6, plus an
   **"Ungraded"** bar for organisations that couldn't be graded.
2. **Average sovereignty by sector** — the average grade per organisation type
   (city, hospital, university, courthouse, …).
3. **Hosting residency** — where the mail is hosted, grouped into Germany, EU,
   other, and US.

### 3.3 The map

The map shows every (geolocated) organisation as a coloured pin, where the colour is
its sovereignty grade (green = sovereign … dark red = not sovereign).

- **Clusters** — nearby pins are grouped into numbered clusters; zoom in or click a
  cluster to expand it.
- **Search** — use the search bar on the map to jump to a place.
- **Click a pin** — a popup shows the organisation's name, domain, type, its grade
  (`level (index/6)`), and a per-role breakdown of its mail flow: for inbound mail,
  the mailbox, outbound mail and webmail it lists the detected software, a coloured
  category tag, the hosting country flags, and — if present — the security relay
  ("via …") that sits in front. The popup also shows when the data was last checked.
- **Legend** — the legend (corner of the map) explains the pin colours.
- **Filters** — click the filter button to narrow the map (and the table) by
  provider, vendor class, organisation category, or country. The button shows how
  many filters are active. Filters apply to both the map and the table at the same
  time.

### 3.4 The organisation table

Below the map, a searchable, paginated table lists the organisations with columns
for: domain, organisation, category, provider, software, **class** (the vendor
category, as a coloured badge), **hosting** (country flags), **status** (the
sovereignty level), and **score** (`index/6`).

- **Search** — type in the search box to filter rows by any visible field.
- **Active filters** appear as removable chips above the table; click a chip's ×
  to remove that filter, or "clear all" to reset.
- **Pagination** — 10 rows per page; use the page numbers or prev/next.

---

## 4. Reading a sovereignty grade

The grade combines several signals:

- where the mail **servers** are physically located,
- who **hosts** them (an EU operator vs. a US hyperscaler),
- what **kind of vendor** makes the mail software,
- where that **vendor** is based,
- whether the software is **open source** or proprietary.

A key detail: if a sovereign mail server sits **behind a foreign security filter**
(a "proxy", e.g. Proofpoint in the US), the mail still passes through that filter,
so that path is rated by the weaker of the two. This is why an otherwise sovereign
organisation can still receive a poorer grade. The full method is explained on the
**Score Info** page.

---

## 5. Frequently asked questions

**Why do some organisations show no grade?**
Some organisations can't be graded — often we can see where their mail is hosted but
not which software runs it. They are still shown (in grey, as "unknown") but kept out
of the grade-based statistics so the averages aren't skewed by guesses. Only
organisations where no mail system was found at all are omitted entirely.

**Why does a German organisation have a red grade?**
Most often because its mail is run on Microsoft 365 / Google Workspace, or because a
US security filter sits in front of an otherwise sovereign server. Open the map
popup or the table to see the detected software and hosting.

**How current is the data?**
Each organisation's popup shows a "last checked" timestamp, and the overview cards
compare the latest scan to the previous one.

**Can I change the language?**
Yes — use the DE / EN toggle in the navigation bar. The choice is saved in your
browser.
