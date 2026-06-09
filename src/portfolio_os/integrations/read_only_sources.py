from __future__ import annotations

from portfolio_os.db.connection import Database
from portfolio_os.integrations.repositories import ReadOnlyIntegrationRepository


class ReadOnlyIntegrationService:
    def __init__(self, db: Database) -> None:
        self.repo = ReadOnlyIntegrationRepository(db)

    def register_source(self, source_name: str, source_type: str, read_only_confirmed: bool, authority_boundary_note: str, connection_descriptor_json: str = "{}"):
        return self.repo.register_source(source_name, source_type, read_only_confirmed, authority_boundary_note, connection_descriptor_json)

    def record_import(self, integration_source_id: int, import_scope: str, import_status: str, artifact_path: str | None = None, rows_seen: int = 0, rows_imported: int = 0, checksum: str | None = None, notes: str | None = None):
        return self.repo.record_import(integration_source_id, import_scope, import_status, artifact_path, rows_seen, rows_imported, checksum, notes)
