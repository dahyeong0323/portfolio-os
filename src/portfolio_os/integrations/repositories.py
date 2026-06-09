from __future__ import annotations

from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.integrations.models import ReadOnlyImportRun, ReadOnlyIntegrationSource
from portfolio_os.validators import datetime_from_text, require_text


def _bool(value: Any) -> bool:
    return bool(int(value))


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def source_from_row(row: dict[str, Any]) -> ReadOnlyIntegrationSource:
    return ReadOnlyIntegrationSource(
        row["integration_source_id"],
        row["source_name"],
        row["source_type"],
        _bool(row["read_only_confirmed"]),
        row["authority_boundary_note"],
        row["connection_descriptor_json"],
        _bool(row["is_active"]),
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def import_run_from_row(row: dict[str, Any]) -> ReadOnlyImportRun:
    return ReadOnlyImportRun(row["import_run_id"], row["integration_source_id"], row["import_scope"], row["import_status"], row["artifact_path"], row["rows_seen"], row["rows_imported"], row["checksum"], row["notes"], _dt(row["created_at"]))


class ReadOnlyIntegrationRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def register_source(self, source_name: str, source_type: str, read_only_confirmed: bool, authority_boundary_note: str, connection_descriptor_json: str = "{}") -> ReadOnlyIntegrationSource:
        require_text(source_name, "source_name")
        require_text(authority_boundary_note, "authority_boundary_note")
        if not read_only_confirmed:
            raise ValueError("read_only_confirmed must be true for Stage 5 integration sources")
        cursor = self.db.execute(
            """
            INSERT INTO read_only_integration_sources(source_name, source_type, read_only_confirmed, authority_boundary_note, connection_descriptor_json)
            VALUES (?, ?, 1, ?, ?)
            """,
            (source_name, source_type, authority_boundary_note, connection_descriptor_json),
        )
        self.db.commit()
        return self.get_source(cursor.lastrowid)

    def get_source(self, integration_source_id: int) -> ReadOnlyIntegrationSource:
        row = self.db.fetch_one("SELECT * FROM read_only_integration_sources WHERE integration_source_id = ?", (integration_source_id,))
        if row is None:
            raise ValueError(f"read-only integration source not found: {integration_source_id}")
        return source_from_row(row)

    def record_import(self, integration_source_id: int, import_scope: str, import_status: str, artifact_path: str | None = None, rows_seen: int = 0, rows_imported: int = 0, checksum: str | None = None, notes: str | None = None) -> ReadOnlyImportRun:
        self.get_source(integration_source_id)
        cursor = self.db.execute(
            """
            INSERT INTO read_only_import_runs(integration_source_id, import_scope, import_status, artifact_path, rows_seen, rows_imported, checksum, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (integration_source_id, import_scope, import_status, artifact_path, rows_seen, rows_imported, checksum, notes),
        )
        self.db.commit()
        return self.get_import_run(cursor.lastrowid)

    def get_import_run(self, import_run_id: int) -> ReadOnlyImportRun:
        row = self.db.fetch_one("SELECT * FROM read_only_import_runs WHERE import_run_id = ?", (import_run_id,))
        if row is None:
            raise ValueError(f"read-only import run not found: {import_run_id}")
        return import_run_from_row(row)
