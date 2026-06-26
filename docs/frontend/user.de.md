# S.M.A.R.T. Frontend — Benutzerhandbuch (DE)

Dieses Handbuch erklärt, wie man **die Website nutzt**. Technisches Wissen ist nicht
nötig. Zur Implementierung siehe [technical.de.md](technical.de.md). Englische
Fassung: [user.en.md](user.en.md).

---

## 1. Was die Website zeigt

Die S.M.A.R.T.-Website visualisiert, wie **digital souverän** die E-Mail
öffentlicher Organisationen in Deutschland, Österreich und der Schweiz ist — also
ob sie ihre Mail auf eigener / EU- / offener Infrastruktur betreiben oder von
ausländischen Anbietern wie Microsoft 365 oder Google Workspace abhängen.

Jede Organisation erhält eine einzige **Souveränitätsnote von 1 bis 6**:

| Note | Farbe | Bedeutung |
|---|---|---|
| **1** | grün | sehr souverän |
| **2** | hellgrün | souverän |
| **3** | gelb | gemischt |
| **4** | orange | eher nicht souverän |
| **5** | rot | nicht souverän |
| **6** | dunkelrot | nicht souverän / Hochrisiko |
| — | grau | zu wenig Daten („unbekannt“) |

Niedriger ist besser. Organisationen ohne ausreichende Datenbasis werden im
Dashboard nicht angezeigt.

---

## 2. Die Seiten

Die Site hat drei Seiten, erreichbar über die obere Navigationsleiste:

- **Start (`/`)** — eine einführende Landingpage zu Projekt und
  Souveränitätsgedanke, mit einem Button zum Dashboard.
- **Dashboard (`/dashboard`)** — die interaktive Datenansicht: Kennzahlen, eine
  Insights-Sektion, die Karte und die Organisationstabelle.
- **Score Info (`/score-info`)** — die vollständige Bewertungsmethodik (wie die Note
  1–6 berechnet wird).

Die Oberflächensprache lässt sich über den Umschalter in der Navigationsleiste
zwischen **DE** und **EN** wechseln (Deutsch ist Standard). Die Wahl wird gemerkt.

---

## 3. Das Dashboard

### 3.1 Übersichts-Kennzahlen

Oben findest du zusammenfassende Karten:

- **Gescannte Organisationen** — wie viele Organisationen in den aktuellen Daten
  sind.
- **Souveränitätsindex** — die Durchschnittsnote über alle bewerteten
  Organisationen (niedriger ist besser).
- **Gescannte Domains** — wie viele distinkte E-Mail-Domains untersucht wurden.

Jede Karte zeigt einen kleinen **Trendpfeil**, der den aktuellen Scan mit dem
vorigen vergleicht („seit letztem Scan“). Beim Souveränitätsindex wird ein
*Rückgang* als gute (grüne) Veränderung dargestellt, weil eine niedrigere Note
besser ist.

Unter den Karten zeigen zwei **„Top-Anteile“**-Listen die häufigsten
**Mail-Vendors** (z. B. Microsoft) und **Hosting-Anbieter** mit ihrem Anteil an den
Organisationen.

### 3.2 Insights

Die Insights-Sektion zeigt drei aus den Daten berechnete Balkendiagramme:

1. **Score-Verteilung** — wie viele Organisationen auf jede Note 1–6 entfallen.
2. **Ø-Souveränität je Sektor** — die Durchschnittsnote je Organisationstyp (Stadt,
   Krankenhaus, Universität, Gericht, …).
3. **Hosting-Residenz** — wo die Mail gehostet wird, gruppiert nach Deutschland,
   EU, übrige, USA.

### 3.3 Die Karte

Die Karte zeigt jede (geolokalisierte) Organisation als farbigen Pin, dessen Farbe
ihre Souveränitätsnote ist (grün = souverän … dunkelrot = nicht souverän).

- **Cluster** — nahe Pins werden zu nummerierten Clustern gruppiert; hineinzoomen
  oder ein Cluster anklicken, um es aufzuklappen.
- **Suche** — über die Suchleiste der Karte zu einem Ort springen.
- **Pin anklicken** — ein Popup zeigt Name, Domain, Typ, die Note
  (`Level (Index/6)`) und eine Aufschlüsselung des Mailflusses je Rolle: für
  eingehende Mail, Postfach, ausgehende Mail und Webmail listet es die erkannte
  Software, ein farbiges Kategorie-Tag, die Hosting-Länderflaggen und — falls
  vorhanden — das vorgeschaltete Security-Relay („via …“). Außerdem zeigt das Popup,
  wann die Daten zuletzt geprüft wurden.
- **Legende** — die Legende (Kartenecke) erklärt die Pin-Farben.
- **Filter** — über den Filter-Button die Karte (und die Tabelle) nach Provider,
  Organisationskategorie oder Land einschränken. Der Button zeigt, wie viele Filter
  aktiv sind. Filter wirken gleichzeitig auf Karte und Tabelle.

### 3.4 Die Organisationstabelle

Unter der Karte listet eine durchsuchbare, paginierte Tabelle die Organisationen
mit Spalten für: Domain, Organisation, Kategorie, Provider, Software, **Klasse** (die
Vendor-Kategorie als farbiges Badge), **Hosting** (Länderflaggen), **Status** (das
Souveränitätslevel) und **Score** (`Index/6`).

- **Suche** — im Suchfeld tippen, um Zeilen nach jedem sichtbaren Feld zu filtern.
- **Aktive Filter** erscheinen als entfernbare Chips über der Tabelle; auf das ×
  eines Chips klicken, um diesen Filter zu entfernen, oder „alle löschen“ zum
  Zurücksetzen.
- **Pagination** — 10 Zeilen pro Seite; Seitenzahlen oder Vor/Zurück nutzen.

---

## 4. Eine Souveränitätsnote lesen

Die Note kombiniert mehrere Signale:

- wo die Mail-**Server** physisch stehen,
- wer sie **hostet** (ein EU-Betreiber vs. ein US-Hyperscaler),
- welche **Art von Hersteller** die Mail-Software macht,
- wo dieser **Hersteller** sitzt,
- ob die Software **Open Source** oder proprietär ist.

Ein wichtiges Detail: Sitzt ein souveräner Mailserver **hinter einem ausländischen
Security-Filter** (einem „Proxy“, z. B. Proofpoint in den USA), läuft die Mail
trotzdem durch diesen Filter — dieser Pfad wird daher mit dem schwächeren der
beiden bewertet. Deshalb kann eine sonst souveräne Organisation dennoch eine
schlechtere Note erhalten. Die vollständige Methode erklärt die Seite **Score
Info**.

---

## 5. Häufige Fragen

**Warum fehlen manche Organisationen?**
Organisationen, die nicht bewertet werden konnten (zu wenig Daten), bleiben bewusst
weg, damit die Zahlen nicht durch Schätzungen verzerrt werden.

**Warum hat eine deutsche Organisation eine rote Note?**
Meist, weil ihre Mail auf Microsoft 365 / Google Workspace läuft oder weil ein
US-Security-Filter vor einem sonst souveränen Server sitzt. Öffne das Karten-Popup
oder die Tabelle, um die erkannte Software und das Hosting zu sehen.

**Wie aktuell sind die Daten?**
Das Popup jeder Organisation zeigt einen „zuletzt geprüft“-Zeitstempel, und die
Übersichts-Karten vergleichen den neuesten Scan mit dem vorigen.

**Kann ich die Sprache ändern?**
Ja — über den DE/EN-Umschalter in der Navigationsleiste. Die Wahl wird im Browser
gespeichert.
