# Frontend Stage 1 API Usage

## Install

From the repository root:

```powershell
python -m pip install -e ".[dev]"
```

## Database

The API defaults to `data/portfolio_os.sqlite3`. It never creates or migrates the database.

Initialize a new local database through the existing CLI before running the API:

```powershell
python -m portfolio_os.cli.main init-db
```

To select another database, set:

```powershell
$env:PORTFOLIO_OS_DB_PATH = "C:\path\to\portfolio_os.sqlite3"
```

The optional `PORTFOLIO_OS_APP_MODE` value is reported by `/api/v1/health`. Its default is `local-read-only`.

## Run

```powershell
python -m uvicorn portfolio_os.api.app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/docs
```

## Verify

```powershell
python -m pytest -q
python -m compileall -q src tests
```

The API opens SQLite with URI `mode=ro` and enables `PRAGMA query_only=ON`. Any write attempted through that connection fails at the database layer.
