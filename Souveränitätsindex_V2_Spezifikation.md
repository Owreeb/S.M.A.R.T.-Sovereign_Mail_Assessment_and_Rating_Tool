# Souveränitätsindex V2 - Spezifikation

Stand: 2026-06-10. Bezieht sich auf den flachen JSON-Export des Scanners
(`organizations*.json`) und löst die V1-Fassung mit 10 Markern als
veröffentlichte Struktur ab. V1 bleibt als detailliertes Regelwerk dahinter
erhalten (siehe Abschnitt 7).

Grundskala überall: **1 = sehr souverän ... 6 = nicht souverän** (Schulnoten).

---

## 1. Grundprinzip: drei Stufen

Der Index wird nicht als ein Monolith pro Organisation berechnet, sondern in
drei Stufen. Damit wird sichtbar, wenn einzelne Teilsysteme einer Org in
unterschiedlichen Jurisdiktionen liegen (z.B. Versand in DE, eingehender
Filter in den USA).

1. **Per-System-Score** - jedes Mailsystem (smtp_out, smtp_in, imap_pop3,
   webmailer) bekommt eine Note aus fünf Markern.
2. **Rollen-Score** - pro Rolle wird das vorgeschaltete Proxy-System mit
   einbezogen: `Rolle = max(System-Note, Proxy-Note)`.
3. **Org-Endnote** - die Rollen werden gewichtet zusammengeführt, kombiniert
   mit der schlechtesten Rolle, damit ein US-Ausreißer nicht weggemittelt wird.

---

## 2. Datengrundlage

Pro Mailsystem (und identisch pro Proxy) liefert der Scanner diese Felder:

| Feld | Bedeutung | Marker |
|---|---|---|
| `open_source_rating` | offen vs. proprietär | Technologie |
| `vendor_country_rating` | Sitzland des Herstellers | Technologie |
| `vendor_category_rating` | Anbieterklasse der Software | Anbieter |
| `ips[].country_rating` | Land, in dem die IP betrieben wird | Geografie |
| `ips[].hoster_rating` | Betreiber der IP / des ASN | Anbieter |

Der Proxy ist in der JSON ein verschachteltes Objekt mit **exakt denselben
Feldern** wie ein Mailsystem. Er wird deshalb mit derselben Funktion bewertet.
`proxy: null` bedeutet: kein Proxy vorhanden.

---

## 3. Stufe 1 - Per-System-Score

Gewichteter Mittelwert der fünf Marker:

| Marker | Quelle | Gewicht |
|---|---|---|
| IP-Land | `ips[].country_rating` (Mittel über alle IPs) | 15 |
| IP-Hoster | `ips[].hoster_rating` (Mittel über alle IPs) | 15 |
| Vendor-Kategorie | `vendor_category_rating` | 10 |
| Vendor-Land | `vendor_country_rating` | 10 |
| Open-Source | `open_source_rating` | 10 |

Die Gewichte werden intern auf Summe 1 normiert. **Fehlt ein Marker** (z.B.
keine eigenen IPs, wie bei reinen Software-Proxys), wird er weggelassen und die
übrigen Gewichte proportional hochskaliert. So erzeugen Datenlücken weder
künstlich gute noch schlechte Noten.

Beispiel rspamd (DFN, DE, Open Source, keine IPs): IP-Marker entfallen, übrig
bleiben Vendor-Land 1, Open-Source 1, Vendor-Kategorie 2, also (1+1+2)/3 = **1,33**.

---

## 4. Bewertungsskalen

### 4.1 IP-Land (`country_rating`)

1 = DE, 2 = EU/EWR/CH, 3 = UK oder Drittland mit Angemessenheitsbeschluss,
5 = USA / CLOUD-Act-betroffen, 6 = Hochrisikoland (z.B. RU, CN).

### 4.2 IP-Hoster (`hoster_rating`)

1 = öffentlicher/genossenschaftlicher EU-Betreiber, 2 = privatwirtschaftlicher
EU-Betreiber, 3 = EU-Tochter eines Drittlandkonzerns, 4 = neutraler
internationaler Carrier, 5 = US-Hyperscaler, 6 = sanktionierter Anbieter.

### 4.3 Vendor-Land (`vendor_country_rating`)

Skala analog 4.1, bezogen auf den Sitz des Software-Herstellers.

### 4.4 Open-Source (`open_source_rating`)

1 = Open Source mit aktivem EU-Maintainer, 2 = Open Source ohne EU-Bezug,
4 = proprietär mit offenen Standards (IMAP, SMTP, JMAP), 6 = proprietär mit
Lock-in (z.B. Exchange Online).

### 4.5 Vendor-Kategorie (`vendor_category_rating`) - überarbeitet

Diese Skala war in V1 als "Provider-Kategorie" zu schwach. Sie wird jetzt
analog zum IP-Hoster (4.2) geführt, nur bezogen auf das **Software-Unternehmen**:

| Note | Anbieterklasse der Software |
|---|---|
| 1 | Eigenentwicklung der Org oder gemeinwohlorientiertes EU-Projekt (Verein, Stiftung, Genossenschaft, Community-OSS, DFN) |
| 2 | privatwirtschaftliches EU-Softwareunternehmen (z.B. Open-Xchange GmbH, mailbox.org, Mailcow) |
| 3 | EU-Tochter / Niederlassung eines Drittlandkonzerns |
| 4 | neutraler internationaler Anbieter ohne CLOUD-Act-Bezug |
| 5 | US-Hyperscaler / US-Cloud-Mailkonzern (Microsoft 365, Google) |
| 6 | sanktionierter, verschleierter oder unbekannter Anbieter |

Hinweis: In den aktuellen Daten kommen nur `national` (Rating 2) und
`hyperscaler` (Rating 5) vor. Nach dieser Skala wäre DFN als
gemeinwohlorientierter Träger eher **Note 1**. Der Scanner muss beim Remapping
entsprechend nachgezogen werden.

---

## 5. Stufe 2 - Rollen-Score und Proxy-Regel

Der Proxy steht **vor** dem Mailserver. Die Mail läuft im Klartext durch ihn,
bevor sie den (souveränen) Server erreicht. Ein souveräner Server hinter einem
US-Proxy hat seine Vertraulichkeit auf diesem Pfad bereits verloren. Deshalb:

```
Rollen-Score = max(System-Note, Proxy-Note)
```

Ein Pfad ist nur so souverän wie sein schwächstes Glied. Das ist bewusst hart
auf Rollenebene, weil genau dieser Pfad tatsächlich kompromittiert ist.
Bei `proxy: null` gilt `Rollen-Score = System-Note`. Mehrere Systeme einer
Rolle werden gemittelt.

---

## 6. Stufe 3 - Org-Endnote

Die vier Rollen werden nach Vertraulichkeits-Exposition gewichtet:

| Rolle | Gewicht | Begründung |
|---|---|---|
| imap_pop3 | 30% | gesamtes Postfach (Daten at rest) |
| smtp_in | 25% | gesamter eingehender Verkehr |
| smtp_out | 25% | gesamter ausgehender Verkehr |
| webmailer | 20% | Zugriffsschicht, Klartext + Credentials |

Daraus die Endnote als Kombination aus Mittelwert und schlechtester Rolle:

```
Endnote = 0,6 * gewichteter Mittelwert der Rollen
        + 0,4 * schlechteste Rolle
```

kaufmännisch auf eine Schulnote gerundet. Der Worst-Case-Anteil von 40 Prozent
verhindert, dass eine einzelne nicht-souveräne Rolle weggemittelt wird, ohne
eine sonst saubere Org gleich auf 5 oder 6 zu ziehen. Fehlende Rollen werden
aus der Gewichtung genommen und der Rest renormiert.

---

## 7. Zuordnung zu den fünf V2-Dimensionen (für den Bericht)

V2 fasst die zehn V1-Marker thematisch in fünf Dimensionen zusammen. Veröffentlicht
werden Endnote plus diese fünf Einzelnoten mit Klartextbegründung:

| V2-Dimension | berechnet aus | V1-Marker |
|---|---|---|
| 1 Geografie | IP-Land | M1 |
| 2 Anbieter | IP-Hoster + Vendor-Kategorie | M2, M5 |
| 3 Technologie | Vendor-Land + Open-Source | M3, M4 |
| 4 Architektur | Proxy-max-Regel + Rollen-Split | M6, M7, M8 |
| 5 Datenqualität | Vollständigkeit + Historie | M9, M10 |

Damit ist V2 vollständig aus V1 ableitbar. Zwei V1-Marker entfallen in der
aktuellen Datengrundlage: **M9 (ASN-Konzentration)**, weil die ASN-Felder im
neuen JSON nicht mehr enthalten sind (nur noch `hoster`), und **M7
(In/Out-Konsistenz)**, weil der DE/US-Split durch die Per-Rollen-Bewertung
ohnehin direkt sichtbar wird.

---

## 8. Umgang mit leeren Feldern (n.b.-Regel)

- **Feld technisch nicht ermittelbar** (kein rDNS, kein Hoster auflösbar): Marker
  als nicht bewertbar (n.b.) kennzeichnen und aus der Gewichtung nehmen, Rest
  proportional hochskalieren.
- **Feld leer, aber prinzipiell ermittelbar** (Vendor unbekannt): mit Note 4
  bewerten und als "geschätzt" flaggen. Ein nicht klassifizierbarer Anbieter ist
  selbst ein leichtes Souveränitätssignal (fehlende Transparenz).
- **Ganze Markergruppe fehlt systematisch**: Hinweis "Datenqualität niedrig".
  Stehen pro bewertbarer Rolle im Schnitt mehr als drei der fünf Per-System-Marker
  auf n.b., wird keine Endnote berechnet, sondern Status **n.b.** ausgewiesen.

---

## 9. Rechenbeispiel (verifiziert mit `sovereignty_score.py`)

### Universität Hamburg

| Rolle | System | Proxy | Rolle = max |
|---|---|---|---|
| imap_pop3 | Dovecot 1,17 | nginx 1,33 | 1,33 |
| smtp_in | Postfix 1,17 | **Proofpoint 5,00** | **5,00** |
| smtp_out | Postfix 1,17 | rspamd 1,33 | 1,33 |
| webmailer | Roundcube 1,17 | HAProxy 1,33 | 1,33 |

Mittelwert = 2,25, schlechteste Rolle = 5,00.
Endnote = 0,6 * 2,25 + 0,4 * 5,00 = **3,35 -> Note 3**.

Lesart: souveräner Kern, aber ernste Exposition des eingehenden Verkehrs über
den US-Proofpoint-Filter.

### Stadt München

Alle Rollen 5,17 bis 5,33 (durchgehend Microsoft 365).
Mittelwert = 5,25, schlechteste Rolle = 5,33.
Endnote = **5,28 -> Note 5**.

---

## 10. Offene Punkte / Daten-TODOs

1. **Stammdatentabellen versionieren.** Mapping Vendor -> Sitzland und
   Vendor -> Kategorie sowie Hoster -> Klasse als versioniertes Repo führen und
   mit `scanner_version_git_hash` verknüpfen, damit historische Noten
   reproduzierbar bleiben.
2. **`vendor_category_rating` neu mappen** gemäß Skala 4.5 (DFN -> 1 statt 2).
3. **Open-Source-Skala vollständig belegen.** Aktuell nur 1 und 6 in den Daten;
   Zwischenstufen 2 und 4 fehlen.
4. **ASN-Felder geklärt?** Wenn ASN-Konzentration (V1-M9) erhalten bleiben soll,
   müssen `asn` / `asn_org` wieder in den Export. Sonst Dimension 5 allein über
   Datenvollständigkeit und Historie definieren.
5. **Gewichte kalibrieren.** Rollengewichte, Proxy-Regel (max vs. hoher Blend)
   und die 0,6/0,4-Aufteilung an einem größeren Datensatz gegen das Bauchgefühl
   prüfen.
