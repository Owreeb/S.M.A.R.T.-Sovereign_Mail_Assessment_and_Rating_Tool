# Woher kommen die Einrichtungen? - Datengrundlage Wikidata

## Was ist Wikidata?

[Wikidata](https://www.wikidata.org) ist eine freie, gemeinschaftlich
gepflegte Wissensdatenbank.
Dort ist jede Sache (eine Stadt, ein Krankenhaus, eine Universität) als
Eintrag gespeichert, oft mit Angaben wie Website, E-Mail-Adresse, Standort
und Land.

S.M.A.R.T. holt sich die Liste der zu prüfenden Einrichtungen samt deren
Webseiten und E-Mail-Adressen aus Wikidata. Wir erstellen die Liste also
nicht von Hand, sondern fragen sie automatisch ab.

## Welche Einrichtungen holen wir?

Aus drei Ländern: **Deutschland, Österreich und der Schweiz** und  in
folgenden Bereichen:

Universitäten, Krankenhäuser, Schulen, Gerichte, Städte und Gemeinden,
politische Parteien, Zeitungen

Pro Einrichtung übernehmen wir, falls vorhanden: Name, Website, E-Mail,
Stadt, Bundesland und Land. Aus Website und E-Mail wird die E-Mail Domain hergeleitet und genau diese Domain wird anschließend geprüft.

## Warum taucht eine bestimmte Einrichtung evtl. nicht auf?

Die Liste ist nur so vollständig wie Wikidata. Eine Einrichtung **fehlt**,
wenn einer dieser Punkte zutrifft:

- **Keine Website und keine E-Mail in Wikidata hinterlegt.** Ohne diese
  Angaben gibt es nichts zu prüfen.
- **Die Einrichtung ist gar nicht in Wikidata** oder nur lückenhaft angelegt.
- **Sie ist nicht richtig zugeordnet** z.B. eine Schule, die nicht als
  „Schule“ eingetragen ist, oder ein Eintrag ohne Land.
- **Sie ist als geschlossen/aufgelöst markiert.**

Kurz: Fehlt etwas, liegt das fast immer an **lückenhaften Wikidata-Daten**,
nicht am Tool. Der Vorteil dieser Quelle: Sie ist frei, offen und wird von
der Community laufend ergänzt. Fehlende Einträge lassen sich dort jederzeit
nachpflegen, beim nächsten Durchlauf sind sie dann automatisch dabei.
