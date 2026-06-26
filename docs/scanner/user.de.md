# S.M.A.R.T. Scanner — Benutzerhandbuch (DE)

Dieses Handbuch richtet sich an **Betreiber/innen**, die den Scanner ausführen und
seine Ausgabe verstehen wollen. Interna sind nicht vorausgesetzt — dafür siehe
[technical.de.md](technical.de.md). Englische Fassung: [user.en.md](user.en.md).

---

## 1. Wozu das Werkzeug dient

Der S.M.A.R.T.-Scanner misst, wie **digital souverän** die E-Mail öffentlicher
Organisationen in Deutschland, Österreich und der Schweiz betrieben wird. Für jede
Organisation ermittelt er die eingesetzten Mailprodukte und Hosting-Anbieter und
fasst das zu einer einzigen Schulnote zusammen:

| Note | Bedeutung |
|---|---|
| **1** | sehr souverän (eigene / EU- / öffentliche / Open-Source-Infrastruktur) |
| **2** | souverän |
| **3** | gemischt |
| **4** | eher nicht souverän |
| **5** | nicht souverän (z. B. Microsoft 365 / Google Workspace) |
| **6** | nicht souverän / Hochrisiko oder unbekannt |
| *n.b.* | zu wenig Daten für eine Note (`null` im Export) |

Die Ergebnisse landen in JSON-Dateien, die das Frontend (die öffentliche Website)
einliest.

---

## 2. Voraussetzungen

Du brauchst:

1. **Python 3.12 oder neuer.**
2. **[uv](https://docs.astral.sh/uv/)** — der in diesem Projekt verwendete
   Python-Paket-/Ausführungsmanager.
3. Eine Internetverbindung (der Scanner stellt DNS-, SMTP-, IMAP- und
   WHOIS-Anfragen).

Versionen prüfen:

```bash
python --version      # sollte 3.12+ sein
uv --version
```

---

## 3. Installation

Aus dem Repository-Wurzelverzeichnis:

```bash
cd scanner
uv sync          # legt eine virtuelle Umgebung an und installiert alle Abhängigkeiten
```

Mehr ist nicht nötig — `uv` liest `pyproject.toml`/`uv.lock` und richtet alles ein.

---

## 4. Einen Scan ausführen

Der Hauptlauf scannt alle aktuellen, bereits in der Datenbank gespeicherten Domains
und erzeugt den JSON-Export:

```bash
cd scanner
uv run main.py
```

Was passiert:

1. Ein neuer **Scan-Lauf** wird angelegt (seine ID wird ausgegeben).
2. Die Domains jeder Organisation werden aufgelöst (MX → IP → ASN → SMTP/IMAP/…).
3. Mailprodukte und Hersteller werden per Fingerprint erkannt.
4. Die Ergebnisse werden in der Datenbank gespeichert (mit voller Historie — alte
   Läufe bleiben erhalten).
5. Der JSON-Export wird geschrieben und die Anzahl der Organisationen ausgegeben.

> **Tipp — Testläufe.** Ein voller Scan berührt Tausende Domains und dauert. Zum
> Ausprobieren mit einer kleinen Stichprobe öffne `scanner/main.py` und setze
> `SAMPLE_LIMIT = 50` (oder eine beliebige Zahl). Für einen vollen Lauf wieder auf
> `None` setzen.

### Wo die Datenbank liegt

Die Arbeitsdatenbank ist `scanner/database/SMART.db`. Sie wird beim ersten Lauf
automatisch angelegt.

---

## 5. Die Ausgabe verstehen

Nach einem erfolgreichen Lauf liegen in `scanner/database/export/` diese Dateien:

| Datei | Was es ist |
|---|---|
| `organizations.json` | Die vollständige Liste — ein Eintrag je Organisation, mit Note, Anbietern, Hosting-Ländern und Mailsystemen je Rolle. Diese Datei nutzen Karte und Tabelle des Frontends. |
| `<YYYY-MM-DD>.json` | Eine datierte **Übersicht**: wie viele Organisationen gescannt wurden, wie viele Domains, die Durchschnittsnote sowie die Top-Mail-Vendors und -Hoster. Das Frontend nutzt zwei davon (neueste + vorige) für „seit letztem Scan“-Trends. |
| `*.json.br` | Brotli-komprimierte Kopien (kleiner, gleicher Inhalt). |

### So sieht eine Organisation aus

```jsonc
{
  "org": "Stadt Mannheim",
  "domain": "mannheim.de",
  "category": "city",
  "city": "Mannheim", "state": "Baden-Württemberg", "country": "Deutschland",
  "lat": 49.48, "long": 8.46,
  "last_checked": "2026-06-26T15:42:00Z",
  "sovereignty_index": 5,                 // die Note, 1..6, oder null
  "providers": ["Microsoft"],             // erkannte Software-Hersteller
  "hosters": ["MICROSOFT-CORP-MSN-AS-BLOCK"],
  "mail_systems": { "smtp_in": [ … ], "smtp_out": [ … ], "imap_pop3": [ … ], "webmailer": [ … ] }
}
```

Die vier **Mailsystem-Rollen** sind:

- `smtp_in` — eingehende Mail (der MX-Server, der Mail empfängt).
- `smtp_out` — ausgehende Mail.
- `imap_pop3` — Postfach- / Client-Zugang.
- `webmailer` — browserbasierter Webmail-Zugang.

Jeder Rolle kann ein **Proxy** vorgeschaltet sein (z. B. ein Security-Filter wie
Proofpoint). Das ist für die Note wichtig: sitzt ein souveräner Server hinter einem
US-Proxy, läuft die eingehende Mail trotzdem durch den US-Filter — dieser Pfad wird
daher mit dem schwächeren (weniger souveränen) der beiden bewertet.

---

## 6. Wie die Note entsteht (in einfachen Worten)

Für jedes Mailsystem betrachtet der Scanner bis zu fünf Signale:

- in welchem **Land** die Server-IPs liegen,
- wer diese IPs **hostet** (ein EU-Betreiber? ein US-Hyperscaler?),
- welche **Art von Hersteller** die Software macht (öffentlich? EU-Unternehmen?
  US-Hyperscaler?),
- in welchem **Land** der Software-Hersteller sitzt,
- ob die Software **Open Source** oder proprietär ist.

Daraus entsteht eine Note je System; je Rolle wird das schwächste Glied des Pfads
genommen (Proxy-Regel), und die vier Rollen werden gewichtet zusammengeführt — mit
Extragewicht auf der *schlechtesten* Rolle, damit ein einzelnes ausländisches
System nicht weggemittelt wird. Die vollständige Methodik ist in
[`Souveränitätsindex_V2_Spezifikation.md`](../../Souveränitätsindex_V2_Spezifikation.md)
veröffentlicht und auf der Seite *Score Info* der Website erklärt.

Fehlen für eine Organisation zu viele Daten, wird sie als **n.b.** (nicht bewertbar)
ausgewiesen, statt eine irreführende Note zu erhalten.

---

## 7. Aktualisieren / erneut ausführen

- **Scan wiederholen:** einfach erneut `uv run main.py` ausführen. Die Datenbank
  behält die Historie jedes Laufs; der Export spiegelt stets den neuesten Stand.
- **Neue Daten ins Frontend bringen:** die frisch geschriebene
  `organizations.json` und die datierte `<YYYY-MM-DD>.json` aus
  `scanner/database/export/` nach `frontend/src/data/` kopieren und das Frontend neu
  bauen. Das Frontend nutzt automatisch die zwei neuesten datierten Dateien für
  seine Trendanzeigen.

---

## 8. Organisations-Liste neu aufbauen (fortgeschritten)

Die Liste der Organisationen stammt aus **Wikidata**. Ihr Neuaufbau ist ein
**separater** Schritt und nicht Teil von `main.py`. Er ruft Universitäten,
Krankenhäuser, Schulen, Gerichte und Städte für Deutschland, Österreich und die
Schweiz ab (konfiguriert in `scanner/src/domainlist_pipline/config.yaml`); ein
optionaler Website-Crawler ergänzt fehlende E-Mail-Domains.

Das macht man normalerweise nur, wenn man die Menge der Organisationen erweitern
oder auffrischen will. Das tägliche Scannen nutzt die bereits in der Datenbank
vorhandenen Organisationen.

---

## 9. Fehlerbehebung

**Manche Organisationen haben keine Note (`sovereignty_index: null`).**
Das ist erwartet und korrekt. Es passiert, wenn der Scanner nicht genug Signale
sammeln konnte — oft weil DNS-/SMTP-/IMAP-Proben rate-limitiert wurden oder ein
Timeout hatten, oder weil die Organisation keinen auflösbaren Mailserver hat. Die
Datenqualitäts-Bremse hält bewusst eine Note zurück, statt zu raten.

**Ein ganzer Scan wirkt unterbefüllt (viele fehlende ASN-/Hoster-Felder).**
Ein großer Scan kann DNS- oder WHOIS-Rate-Limits treffen. Es gibt ein
Recovery-Werkzeug, das nur die IP-Adressen ohne Hosting-Info erneut abfragt, sie
ergänzt und einen Re-Export ohne kompletten Neu-Scan erlaubt. Bitte eine/n
Entwickler/in, `enrich_ip_addresses(session)` gefolgt von `write_dump(session)`
auszuführen (siehe technische Doku, §7.4), und den Export erneut zu
veröffentlichen.

**Der Scan ist langsam.**
Das ist für einen vollen Lauf normal (Tausende Domains, je mehrere
Netzwerk-Proben). Für schnelle Tests `SAMPLE_LIMIT` nutzen.

**`uv: command not found`.**
Zuerst uv installieren (siehe
[uv-Installation](https://docs.astral.sh/uv/getting-started/installation/)), dann
`uv sync` erneut ausführen.
