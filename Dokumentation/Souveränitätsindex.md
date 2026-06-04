# Souveränitätsindex

## V1: 10 Marker:

1. **Hosting-Jurisdiktion (IP_ADDRESSES.country_code, Gewicht 15 Prozent).**  
   1 = DE,  
   2 = EU/EWR/CH,  
   3 = UK,  
   4 = sicheres Drittland mit Angemessenheitsbeschluss,  
   5 = USA/CLOUD Act-betroffen,  
   6 = Hochrisikoland (z.B. RU, CN).

2. **Hosting-Betreiber bzw. ASN-Eigentümer (IP_ADDRESSES.asn_org, Gewicht 15 Prozent).**  
   1 = öffentlicher/genossenschaftlicher EU-Betreiber,  
   2 = privatwirtschaftlicher EU-Betreiber,  
   3 = EU-Tochter eines Drittlandkonzerns,  
   4 = neutraler internationaler Carrier,  
   5 = US-Hyperscaler (AWS, GCP, Azure, MS365),  
   6 = sanktionierter oder hochrisiko-Provider.

3. **Software-Vendor-Sitz (MAIL_SYSTEMS.vendor abgeglichen mit Stammdaten, Gewicht 10 Prozent).**  
   Skala analog zu Marker 1.

4. **Open-Source-Status (MAIL_SYSTEMS.is_open_source, Gewicht 10 Prozent).**  
   1 = Open Source unter OSI-Lizenz mit aktivem EU-Maintainer,  
   3 = Open Source ohne EU-Bezug,  
   5 = proprietär mit offenen Schnittstellen,  
   6 = proprietär und Lock-in.

5. **Provider-Kategorie (MAIL_SYSTEMS.provider_category, Gewicht 10 Prozent).**  
   1 = Eigenbetrieb On-Premises,  
   2 = EU-Managed-Service,  
   3 = EU-SaaS,  
   4 = internationaler Spezialanbieter,  
   5 = US-Cloud-Mailservice,  
   6 = unbekannter oder verschleierter Anbieter.

6. **Proxy- bzw. Vorschalt-Setup (ORG_MAIL_SYSTEM_HISTORY.proxy_system_id, Gewicht 10 Prozent).**  
   Bewertet wird die Note des vorgeschalteten Systems, weil ein US-Proxy vor einem EU-Mailserver die Inhalte trotzdem abgreifbar macht.  
   Kein Proxy = Note ergibt sich aus dem Mailsystem;  
   US-Proxy = 5 oder 6.

7. **Konsistenz Eingang/Ausgang (smtp_in vs. smtp_out je Org, Gewicht 10 Prozent).**  
   1 = beide Wege bei souveränem Anbieter,  
   3 = ein Weg souverän, ein Weg neutral,  
   6 = beide Wege bei US-Hyperscaler.  
   Erkennt Fälle, in denen nach außen MX EU zeigt, ausgehend aber über M365 läuft.

8. **rDNS-Plausibilität (IP_ADDRESSES.rdns_hostname vs. email_domain, Gewicht 5 Prozent).**  
   1 = rDNS gehört zur Org-Domain (echter Eigenbetrieb),  
   3 = rDNS gehört zum erkennbaren Anbieter,  
   6 = rDNS zeigt versteckten Drittanbieter.

9. **ASN-Konzentration (Anzahl distinkter ASNs je Org-Mailsystem-Verbund, Gewicht 5 Prozent).**  
    1 = mehrere unabhängige ASNs in EU,  
    3 = ein ASN in EU,  
    5 = ein ASN bei Hyperscaler,  
    6 = mehrere ASNs aber alle im selben Hyperscaler-Konzern (Scheinredundanz).

10. **Stabilität und Migration (Auswertung der History-Tabellen über SCANNER_RUNS, Gewicht 10 Prozent).**  
    1 = stabile EU-Lösung über viele Scans,  
    3 = wenig Bewegung,  
    5 = Migration Richtung Hyperscaler erkennbar,  
    6 = mehrfach hin und her oder gerade in Migration ohne klares Ziel.

### Erläuterung:
Gewichteter Mittelwert über die zehn Noten, anschließend auf eine Schulnote gerundet (kaufmännisch). Veröffentlicht werden immer die Einzelnoten plus Endnote, plus eine Klartextbegründung je Marker (z.B. "Marker 2: Note 5, weil ASN AS16509 Amazon Technologies"). Damit ist der Index ohne Tool nachvollziehbar.

#### Umgang mit leeren Feldern und Edge Cases:

a) Feld leer, weil technisch nicht ermittelbar (z.B. kein rDNS, kein asn_org auflösbar). Hier wird der Marker als nicht bewertbar gekennzeichnet (Code n.b.) und aus der Gewichtung herausgenommen. Die übrigen Gewichte werden proportional hochskaliert, damit die Summe wieder 100 Prozent ergibt. Im Bericht steht "Marker x: n.b., Begründung". Diese Variante verhindert, dass Datenlücken künstlich gute oder schlechte Noten erzeugen.
b) Feld leer, aber Information könnte vorhanden sein (Vendor unbekannt, Provider-Kategorie nicht klassifiziert). Hier wird mit Note 4 (ausreichend) bewertet und mit Flag geschätzt markiert. Begründung: ein nicht klassifizierbarer Anbieter ist selbst ein leichtes Souveränitätssignal, denn Transparenz fehlt. Note 4 ist neutral genug, um die Org nicht zu Unrecht abzustrafen, aber transparent genug, um zur Nacherfassung zu motivieren.
c) Alle Felder eines Markers fehlen systematisch (z.B. ganze IP-Kette nicht auflösbar). Dann gilt Regel a, zusätzlich wird im Bericht ein Hinweis Datenqualität niedrig ausgegeben. Wenn mehr als drei der zehn Marker auf n.b. stehen, wird keine Endnote berechnet, sondern Status nicht bewertbar (n.b.) ausgewiesen. Eine schlechte Note bei dünner Datenlage wäre nicht nachvollziehbar.

#### Transparenzregeln
* Jede Note muss aus einem oder maximal zwei Datenbankfeldern herleitbar sein. Keine Black-Box-Scores, kein Schätzen. 
* Die Zuordnungstabellen für ASN-Org zu Hyperscaler-Klasse und für Vendor zu Sitzland werden als versioniertes Stammdaten-Repo geführt und mit dem scanner_version_git_hash in SCANNER_RUNS verknüpft, damit historische Noten reproduzierbar bleiben.

---
## V2: 5 Marker:

### Grundprinzip: 
Jeder Marker fragt eine fachliche Frage. Diese Frage wird über eine Kaskade von Datenquellen beantwortet. Die erste verfügbare Quelle bestimmt die Note, die nachfolgenden dienen als Fallback. So bleibt der Index auch bei Lücken im Datenmodell verlässlich.

1. **Geografische Souveränität (Gewicht 25 Prozent)**  
Frage: Wo wird die Mail-Infrastruktur physisch betrieben?

a) IP_ADDRESSES.country_code zum aktuellen MAIL_SYSTEM_IP_HISTORY-Eintrag, sonst  
b) abgeleitet aus IP_ADDRESSES.asn_org gegen Stammdaten-Sitzland, sonst  
c) Top-Level-Domain aus ORG_DOMAIN_HISTORY.email_domain (z.B. .de, .eu), sonst  
d) ORGANISATIONS.country als schwächster Fallback.  

Note: 1 = DE, 2 = EU/EWR/CH, 3 = UK oder Drittland mit Angemessenheit, 5 = USA, 6 = Hochrisikoland. Bei jedem Schritt nach unten wird im Bericht das Konfidenz-Flag um eine Stufe gesenkt.

2. **Anbieter-Souveränität (Gewicht 25 Prozent)**  
Frage: Wer kontrolliert den Betrieb des Mailsystems?  

a) MAIL_SYSTEMS.provider_category, sonst  
b) IP_ADDRESSES.asn_org gegen Klassifikationsliste (Hyperscaler vs. EU-Provider vs. Eigenbetrieb), sonst  
c) MAIL_SYSTEMS.vendor, sonst  
d) Heuristik aus rDNS-Hostname (z.B. outlook.com, amazonaws.com, ovh.net).  

Note 1 = Eigenbetrieb der Organisation oder gemeinwohlorientierter EU-Anbieter (Stiftung, Verein, Genossenschaft, kleine GmbH mit Privacy-Mission), Note 2 = regulärer kommerzieller EU-Provider, 3 = EU-Tochter Drittland, 5 = US-Hyperscaler, 6 = sanktionierter Anbieter.

3. **Technologie-Souveränität (Gewicht 20 Prozent)**  
Frage: Ist die eingesetzte Software offen und unabhängig?  

a) MAIL_SYSTEMS.is_open_source und MAIL_SYSTEMS.software, sonst  
b) MAIL_SYSTEMS.software allein gegen OSS-Stammdatenliste, sonst  
c) Banner-Heuristik aus MAIL_SYSTEMS.software (z.B. Postfix, Exim, Dovecot = OSS), sonst  
d) MAIL_SYSTEMS.vendor zur groben Einordnung.  

Note: 1 = OSS mit EU-Maintainer, 2 = OSS ohne EU-Bezug, 4 = proprietär mit offenen Standards (IMAP, SMTP, JMAP), 6 = proprietär und Lock-in (Exchange Online).  

4. **Architektur-Souveränität (Gewicht 15 Prozent)**  
Frage: Ist die Org Herr ihrer Daten oder hat sie ausgelagert bzw. eine Drittpartei vorgeschaltet?  

a) ORG_MAIL_SYSTEM_HISTORY.proxy_system_id vorhanden und proxy_system zeigt auf abweichende Jurisdiktion oder Anbieter, sonst  
b) Vergleich der MAIL_SYSTEMS mit role smtp_in und smtp_out derselben Org: weicht der Out-Provider vom In-Provider ab, sonst  
c) rDNS-Hostname aus IP_ADDRESSES vs. email_domain aus ORG_DOMAIN_HISTORY: passt der rDNS zur eigenen Domain.  

Note: 1 = ein konsistenter Eigenbetrieb, 2 = ein konsistenter EU-Dienstleister, 3 = transparenter Spam-Filter-Proxy in EU, 5 = vorgeschalteter US-Proxy vor EU-Server, 6 = mehrstufige Auslagerung in unterschiedliche Drittlandzonen.

5. **Datenqualität und Historie (Gewicht 15 Prozent)**  
Frage: Wie belastbar ist die Bewertung und wie stabil ist die Situation?  

a) Anzahl bewertbarer Marker eins bis vier (je mehr Primärquellen verfügbar, desto besser), kombiniert mit  
b) Anzahl SCANNER_RUNS, in denen die ORG_MAIL_SYSTEM_HISTORY stabil war (is_current über mehrere Runs), kombiniert mit  
c) Anzahl Wechsel in MAIL_SYSTEM_IP_HISTORY pro Org im letzten Jahr.  

Note: 1 = alle Primärquellen vorhanden und Setup stabil über mehr als sechs Runs, 3 = teilweise Fallbacks nötig oder leichte Bewegung, 5 = überwiegend Fallbacks und häufige Wechsel, 6 = Setup gerade in Migration ohne erkennbares Ziel oder fast keine belastbaren Daten.
Aggregation und Umgang mit Lücken

Endnote ist der gewichtete Mittelwert der fünf Marker, kaufmännisch auf eine Schulnote gerundet. Da jeder Marker über die ODER-Kaskade fast immer ein Ergebnis liefert, fällt eine Marker-Note nur in extremen Datenlücken aus. Wenn doch, wird der entsprechende Anteil proportional auf die übrigen Marker verteilt. Marker 5 bestraft Datenlücken bereits implizit, indem er Fallback-Tiefen in eine schlechtere Note umsetzt. Das ersetzt die n.b.-Mechanik aus dem 10-Marker-Vorschlag und macht den Index kompakter.

Transparenz im Bericht: pro Marker werden die genutzte Quelle, das gelieferte Rohdatum und die Konfidenzstufe ausgewiesen. Beispiel: "Marker 1: Note 5, Quelle a (country_code = US, IP 52.96.x.x), Konfidenz hoch." So bleibt für Leser ohne Toolzugang erkennbar, warum eine Note zustande kam und welcher Fallback aktiv war.