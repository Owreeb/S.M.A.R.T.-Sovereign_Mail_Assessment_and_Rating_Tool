# Entwicklungskonventionen

Die verbindlichen Teamkonventionen für das S.M.A.R.T.-Projekt. Grundlage ist das `DEVELOPMENT.md` im Repository-Root (Stand: 26.03.2026).

## Branching-Strategie

| Branch | Zweck |
|---|---|
| `main` | Produktionsreifer Code -- kein direkter Commit |
| `feature/<name>` | Neue Funktionalität |
| `bugfix/<name>` | Fehlerbehebung |
| `chore/<name>` | Refactoring, Abhängigkeits-Updates, CI/CD-Anpassungen |

Regeln: Immer von `main` abzweigen. Branches klein und fokussiert halten. Kein direkter Commit auf `main`.

## Pull Requests

### Namenskonvention

```
<type>: <kurze Beschreibung>
```

| Typ | Zweck |
|---|---|
| `feat:` | Neue Funktionalität |
| `fix:` | Fehlerbehebung |
| `refactor:` | Code-Verbesserung ohne Funktionsänderung |
| `chore:` | Wartung (Abhängigkeiten, Konfiguration) |

Beispiele: `feat: add statistics grid component`, `fix: overpass retry not resetting`, `chore: update mantine to v8`

### PR-Template

```
## What
Kurze Beschreibung der Änderung

## Notes
Optionale Zusatzinformationen

Implementierer:
- [ ] Ich habe geprüft, dass meine Implementierung alle Akzeptanzkriterien des Jira-Tickets abdeckt
- [ ] Ich habe einen Unit-/E2E-Test für das neue Feature implementiert oder erweitert

Reviewer:
- [ ] Ich habe geprüft, dass die Implementierung alle Akzeptanzkriterien des Jira-Tickets abdeckt
- [ ] Ich habe den Unit-/E2E-Test für das neue Feature geprüft oder erweitert
```

### Definition of Done

Ein PR gilt als abgeschlossen, wenn alle folgenden Punkte erfüllt sind:

- Code kompiliert fehlerfrei
- Alle automatisierten Tests laufen durch
- Mindestens ein Reviewer hat approved
- Alle Review-Kommentare sind aufgelöst
- Dokumentation ist aktualisiert, sofern relevant

### Approval-Regeln

Mindestens 1 Approval erforderlich. Merge ist nicht möglich bei offenen Kommentaren oder fehlendem Approval.

## Coding Standards

### Namenskonventionen

| Typ | Stil | Beispiel |
|---|---|---|
| Klassen / Typen / Interfaces | PascalCase | `StatisticsData` |
| Funktionen / Methoden | camelCase | `getDiffOrZero()` |
| Variablen | camelCase | `currentData` |
| Konstanten | SCREAMING_SNAKE_CASE | `OVERPASS_URLS` |

### Architektur & Struktur

Bestehende Projektmuster einhalten. Vorhandene Logik wiederverwenden, keine Duplikate einführen (DRY-Prinzip).

### Fehlerbehandlung & Logging

Fehler explizit behandeln -- keine stillen Fehler. Strukturiertes Logging konsistent einsetzen.

### Testing

Unit-Tests für alle Business-Logik. Edge Cases abdecken. Externe Abhängigkeiten in Tests mocken. Mindest-Code-Coverage noch festzulegen.

### Allgemeine Regeln

- Secrets in Umgebungsvariablen -- niemals committen
- Debug-Ausgaben vor dem Merge entfernen
- Komplexe oder unklare Logik kommentieren

## CI/CD-Pipeline

### Trigger

- Jeder Pull Request
- Jeder Push auf `main`

### Pipeline-Stufen

- Build
- Tests ausführen
- SonarCloud-Analyse (Projekt: `Owreeb_SMART`)
- Weitere Stufen noch festzulegen

### Regel

Ein PR kann nicht gemergt werden, wenn die Pipeline fehlschlägt. Bei einem defekten Pipeline hat die Reparatur höchste Priorität.

## Ticketsystem

Das Team nutzt **Jira** zur Aufgabenverwaltung. PR-Checklisten referenzieren Jira-Tickets. Konkrete Jira-Instanz und Projektkey sind in diesem Dokument noch zu ergänzen.
