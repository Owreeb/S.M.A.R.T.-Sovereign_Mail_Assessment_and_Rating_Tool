# Scanner

## Run The Bronze Pipeline

### Prerequisites

1. Python 3.12+
2. uv

### Install Dependencies

```powershell
cd scanner
uv sync
```

### Start Pipeline

```powershell
uv run python main.py run_bronze
```

The SQLite database is written to scanner/database/domainlist.db.
