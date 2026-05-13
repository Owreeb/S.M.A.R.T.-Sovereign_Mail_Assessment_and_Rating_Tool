# S.M.A.R.T. -- Projektübersicht

**Sovereign Mail Assessment and Rating Tool**

## Ziel des Projekts

S.M.A.R.T. ist ein Werkzeug zur Bewertung der E-Mail-Infrastruktur-Souveränität deutscher öffentlicher Institutionen. Es soll erkennbar machen, ob Behörden, Gerichte, Schulen und ähnliche Einrichtungen ihre E-Mail-Kommunikation mit eigener oder souveräner Infrastruktur betreiben -- oder ob sie auf externe Anbieter wie Microsoft 365 oder Google Workspace angewiesen sind.

Das Projekt wird als Studierendenprojekt an der Hochschule Karlsruhe im Auftrag der **audriga GmbH, Karlsruhe** durchgeführt.

## Projektstatus

Das Projekt befindet sich in der frühen Entwicklungsphase. Der Scanner hat eine erste lauffähige Pipeline (Bronze Pipeline), das Frontend hat erste Komponenten und ein definiertes Datenmodell.

## Systemüberblick

Das System besteht aus zwei Hauptkomponenten:

- **Scanner:** Sammelt Institutionsdaten aus OpenStreetMap, analysiert DNS-Einträge und Mail-Indikatoren und berechnet einen Souveränitäts-Score. Die Implementierungssprache ist noch offen (zur Diskussion stehen TypeScript/Node.js, Java, Python und andere).
- **Frontend (React/TypeScript):** Single Page Application zur interaktiven Darstellung der Ergebnisse, inkl. Kartenansicht und Filteroptionen.

## Fachlicher Kontext

Für die Bewertung der Mail-Souveränität werden primär folgende technische Merkmale ausgewertet:

- MX Record: Zeigt auf welchen Mailserver eingehende E-Mails geroutet werden (z.B. Exchange/O365 vs. Postfix/DFN)
- SPF Record: Gibt an, welche Server im Namen der Domain Mails versenden dürfen
- IMAP Server: Hinweis auf den genutzten Mailclient-Zugang
- Webmail Gateway: Der Login-Screen eines Webmailers lässt oft auf das eingesetzte Produkt schliessen

Entscheidungslogik (Beispiel): Wenn der MX Record auf einen Microsoft Exchange-Server auflöst, wird angenommen, dass die Institution Microsoft 365 nutzt. Wenn der MX Record auf Postfix zeigt, könnte dahinter eine selbst betriebene oder über DFN bereitgestellte Infrastruktur stehen.

## Geplante Institutionskategorien

Bisher über OpenStreetMap abgefragt:
- Rathäuser (`amenity=townhall`)
- Gerichte (`amenity=courthouse`)

Geplant, noch nicht implementiert:
- Ministerien
- Schulen
- Universitäten
- Weitere Behörden

Möglicherweise auszuklammern: Automobilindustrie (Audi, VW, Mercedes), da diese nicht zur Zielgruppe öffentlicher Institutionen gehören.

## Auftraggeber

**audriga GmbH**
Karlsruhe

Spezialisiert auf E-Mail-Migration und Mailbox-Management. Das Tool soll audriga Einblicke in den deutschen Markt für E-Mail-Infrastruktur im öffentlichen Sektor geben.

## Beteiligte

Studierendenteam, 6. Semester Wirtschaftsinformatik, Hochschule Karlsruhe -- im Rahmen des Angewandten Wissenschaftsprojekts (AWP).

## Weiterführende Dokumente

- [01 Systemarchitektur](01_Architektur.md)
- [02 Scanner-Dokumentation](02_Scanner.md)
- [03 Frontend-Dokumentation](03_Frontend.md)
- [04 Entwicklungsumgebung einrichten](04_Entwicklungsumgebung.md)
- [05 Entwicklungskonventionen](05_Entwicklungskonventionen.md)
