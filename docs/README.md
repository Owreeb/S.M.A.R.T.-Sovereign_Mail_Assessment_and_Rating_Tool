# S.M.A.R.T. — Documentation / Dokumentation

**S**overeign **M**ail **A**ssessment and **R**ating **T**ool — a tool that
measures the digital sovereignty of public-sector e-mail infrastructure in the DACH
region (Germany, Austria, Switzerland), built for **audriga GmbH**.

This folder contains the full **technical** and **user** documentation for both the
**scanner** and the **frontend**, in **English** and **German**.

*Dieser Ordner enthält die vollständige **technische** und **Benutzer**-Dokumentation
für **Scanner** und **Frontend**, auf **Englisch** und **Deutsch**.*

---

## Documentation map / Dokumentationsübersicht

| Component | Audience | English | Deutsch |
|---|---|---|---|
| **Scanner** | Technical / Technisch | [scanner/technical.en.md](scanner/technical.en.md) | [scanner/technical.de.md](scanner/technical.de.md) |
| **Scanner** | User / Benutzer | [scanner/user.en.md](scanner/user.en.md) | [scanner/user.de.md](scanner/user.de.md) |
| **Frontend** | Technical / Technisch | [frontend/technical.en.md](frontend/technical.en.md) | [frontend/technical.de.md](frontend/technical.de.md) |
| **Frontend** | User / Benutzer | [frontend/user.en.md](frontend/user.en.md) | [frontend/user.de.md](frontend/user.de.md) |

---

## Which document do I need? / Welches Dokument brauche ich?

**English**

- *"How do I run the scanner / read its output?"* → [scanner/user.en.md](scanner/user.en.md)
- *"How is the scanner built, what's the DB schema, how is the score computed?"* → [scanner/technical.en.md](scanner/technical.en.md)
- *"How do I use the website?"* → [frontend/user.en.md](frontend/user.en.md)
- *"How is the frontend built, what's the data model, how do I deploy it?"* → [frontend/technical.en.md](frontend/technical.en.md)

**Deutsch**

- *„Wie führe ich den Scanner aus / lese seine Ausgabe?“* → [scanner/user.de.md](scanner/user.de.md)
- *„Wie ist der Scanner aufgebaut, wie das DB-Schema, wie entsteht die Note?“* → [scanner/technical.de.md](scanner/technical.de.md)
- *„Wie nutze ich die Website?“* → [frontend/user.de.md](frontend/user.de.md)
- *„Wie ist das Frontend aufgebaut, was ist das Datenmodell, wie deploye ich es?“* → [frontend/technical.de.md](frontend/technical.de.md)

---

## System at a glance / System auf einen Blick

```
   Wikidata ──► Scanner (Python) ──► SQLite ──► JSON export ──► Frontend (React) ──► static hosting
                DNS/MX/IP/ASN          SCD-2     organizations.json   map · table · stats
                SMTP/IMAP probes       history   <date>.json
                signature matching               (sovereignty index 1..6)
```

- The **scanner** (`scanner/`) discovers each organisation's mail infrastructure,
  fingerprints the products/vendors, derives a **sovereignty grade (1 = very
  sovereign … 6 = not sovereign)**, and exports JSON.
- The **frontend** (`frontend/`) bundles that JSON at build time and renders an
  interactive map, statistics dashboard and filterable table.

The grade methodology ("Souveränitätsindex V2") is specified in
[`../Souveränitätsindex_V2_Spezifikation.md`](../Souveränitätsindex_V2_Spezifikation.md)
and shown on the website's *Score Info* page.

---

## Quick start / Schnellstart

**Scanner** (Python 3.12+, [uv](https://docs.astral.sh/uv/)):

```bash
cd scanner
uv sync
uv run main.py        # → scanner/database/export/organizations.json
```

**Frontend** (Node 22+):

```bash
cd frontend
npm install
npm run dev           # → http://localhost:5173
```

---
