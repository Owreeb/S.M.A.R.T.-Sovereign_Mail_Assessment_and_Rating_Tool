# Entwicklungsumgebung einrichten

## Voraussetzungen (Frontend)

| Tool | Version | Zweck |
|---|---|---|
| Node.js | 22 | Frontend-Laufzeitumgebung |
| npm | (mit Node) | Paketverwaltung für das Frontend |
| Git | aktuell | Versionskontrolle |

## Voraussetzungen (Scanner)

Die Laufzeitumgebung für den Scanner ist noch nicht festgelegt. Dieser Abschnitt wird ergänzt, sobald die Technologieentscheidung getroffen wurde. Kandidaten sind TypeScript/Node.js, Java und Python.

## Repository klonen

```bash
git clone https://github.com/Owreeb/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool.git
cd S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool
```

## Scanner einrichten

Dieser Abschnitt wird nach der Technologieentscheidung ergänzt.

## Frontend einrichten

```bash
cd frontend
npm install
```

### Frontend-Dev-Server starten

```bash
npm run dev
```

Öffnet die Anwendung unter `http://localhost:5173` (Vite-Standard). Änderungen werden automatisch im Browser übernommen (Hot Reload).

### Tests ausführen

```bash
npm run test
```

### Produktions-Build erstellen

```bash
npm run build
```

Der Build-Output landet unter `frontend/dist/`.

## Git-Hooks (Husky)

Die Git-Hooks werden automatisch beim ersten `npm install` eingerichtet. Vor jedem Commit werden alle staged Dateien automatisch formatiert und gelintet. Schlägt der Hook fehl, wird der Commit abgebrochen -- die Fehlermeldung zeigt, was zu korrigieren ist.

Manuell formatieren:

```bash
npm run format
```

Manuell linten:

```bash
npm run lint
```

## CI/CD

GitHub Actions führt bei Pull Requests auf `main` automatisch Lint- und Build-Checks für das Frontend durch. SonarCloud analysiert die Codequalität. Beide Checks müssen grün sein, bevor ein Merge sinnvoll ist. Schlägt die Pipeline fehl, hat die Reparatur höchste Priorität (siehe [Entwicklungskonventionen](05_Entwicklungskonventionen.md)).

SonarCloud-Dashboard: [https://sonarcloud.io/project/overview?id=Owreeb_SMART](https://sonarcloud.io/project/overview?id=Owreeb_SMART)

## Empfohlene Entwicklungsumgebung

Visual Studio Code mit folgenden Erweiterungen:

- **ESLint** (Microsoft) -- zeigt Lint-Fehler direkt im Editor
- **Prettier - Code formatter** -- formatiert beim Speichern
- **SQLite Viewer** -- lässt die `domainlist.db` direkt im Editor inspizieren

Weitere Erweiterungen werden nach der Technologieentscheidung für den Scanner ergänzt.
