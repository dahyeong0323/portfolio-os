from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from fastapi import Request

from portfolio_os.api.errors import ApiError
from portfolio_os.db import Database
from portfolio_os.db.migrations import default_migrations_dir

DEFAULT_DB_PATH = Path("data/portfolio_os.sqlite3")
DEFAULT_APP_MODE = "local-operating-loop"
DEFAULT_SNAPSHOT_DIR = Path("data/imports/account_snapshots")
DEFAULT_REPORT_DIR = Path("data/exports/reconciliation_reports")
DEFAULT_UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024
REQUIRED_API_TABLES = {
    "accounts",
    "instruments",
    "reconciliation_snapshots",
    "transaction_intents",
    "risk_validation_results",
    "order_tickets",
    "order_ticket_events",
    "manual_execution_logs",
}


@dataclass(frozen=True)
class MigrationReadiness:
    expected_count: int
    applied_count: int
    latest_expected_version: int | None
    latest_applied_version: int | None
    ready: bool


@dataclass(frozen=True)
class DatabaseReadiness:
    reachable: bool
    ready: bool
    migrations: MigrationReadiness


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    configured = db_path if db_path is not None else os.getenv("PORTFOLIO_OS_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


def resolve_app_mode(app_mode: str | None = None) -> str:
    return app_mode or os.getenv("PORTFOLIO_OS_APP_MODE") or DEFAULT_APP_MODE


def resolve_snapshot_dir(snapshot_dir: str | Path | None = None) -> Path:
    configured = snapshot_dir if snapshot_dir is not None else os.getenv("PORTFOLIO_OS_SNAPSHOT_DIR")
    return Path(configured) if configured else DEFAULT_SNAPSHOT_DIR


def resolve_report_dir(report_dir: str | Path | None = None) -> Path:
    configured = report_dir if report_dir is not None else os.getenv("PORTFOLIO_OS_REPORT_DIR")
    return Path(configured) if configured else DEFAULT_REPORT_DIR


def resolve_upload_limit(upload_limit_bytes: int | None = None) -> int:
    if upload_limit_bytes is not None:
        return upload_limit_bytes
    configured = os.getenv("PORTFOLIO_OS_UPLOAD_LIMIT_BYTES")
    return int(configured) if configured else DEFAULT_UPLOAD_LIMIT_BYTES


def _expected_migrations() -> dict[int, str]:
    expected: dict[int, str] = {}
    for migration_path in sorted(default_migrations_dir().glob("*.sql")):
        version = int(migration_path.name.split("_", 1)[0])
        expected[version] = hashlib.sha256(migration_path.read_bytes()).hexdigest()
    return expected


def inspect_database(db_path: Path) -> DatabaseReadiness:
    expected = _expected_migrations()
    empty_migrations = MigrationReadiness(
        expected_count=len(expected),
        applied_count=0,
        latest_expected_version=max(expected, default=None),
        latest_applied_version=None,
        ready=False,
    )
    if not db_path.is_file():
        return DatabaseReadiness(reachable=False, ready=False, migrations=empty_migrations)

    connection: sqlite3.Connection | None = None
    try:
        uri = f"{db_path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("SELECT 1").fetchone()
        try:
            applied_rows = connection.execute(
                "SELECT version, checksum FROM schema_migrations ORDER BY version"
            ).fetchall()
        except sqlite3.Error:
            applied_rows = []
        applied = {int(row["version"]): str(row["checksum"]) for row in applied_rows}
        table_rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        tables = {str(row["name"]) for row in table_rows}
        migrations_ready = bool(applied_rows) and all(applied.get(version) == checksum for version, checksum in expected.items())
        schema_ready = REQUIRED_API_TABLES.issubset(tables)
        readiness = MigrationReadiness(
            expected_count=len(expected),
            applied_count=len(applied),
            latest_expected_version=max(expected, default=None),
            latest_applied_version=max(applied, default=None),
            ready=migrations_ready and schema_ready,
        )
        return DatabaseReadiness(reachable=True, ready=readiness.ready, migrations=readiness)
    except sqlite3.Error:
        return DatabaseReadiness(reachable=False, ready=False, migrations=empty_migrations)
    finally:
        if connection is not None:
            connection.close()


@contextmanager
def open_read_only_database(db_path: Path) -> Iterator[Database]:
    readiness = inspect_database(db_path)
    if not readiness.reachable:
        raise ApiError(503, "database_unavailable", "The Portfolio OS database is not reachable.")
    if not readiness.ready:
        raise ApiError(503, "database_not_ready", "The Portfolio OS database migrations are not ready.")

    database = Database(db_path, read_only=True)
    database.connect()
    try:
        yield database
    finally:
        database.close()


async def get_database(request: Request):
    with open_read_only_database(request.app.state.db_path) as database:
        yield database


@contextmanager
def open_writable_database(db_path: Path) -> Iterator[Database]:
    readiness = inspect_database(db_path)
    if not readiness.reachable:
        raise ApiError(503, "database_unavailable", "The Portfolio OS database is not reachable.")
    if not readiness.ready:
        raise ApiError(503, "database_not_ready", "The Portfolio OS database migrations are not ready.")

    database = Database(db_path)
    database.connect()
    try:
        yield database
    finally:
        database.close()


async def get_writable_database(request: Request):
    with open_writable_database(request.app.state.db_path) as database:
        yield database
