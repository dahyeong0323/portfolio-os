from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReadOnlyIntegrationSource:
    integration_source_id: int
    source_name: str
    source_type: str
    read_only_confirmed: bool
    authority_boundary_note: str
    connection_descriptor_json: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class ReadOnlyImportRun:
    import_run_id: int
    integration_source_id: int
    import_scope: str
    import_status: str
    artifact_path: str | None
    rows_seen: int
    rows_imported: int
    checksum: str | None
    notes: str | None
    created_at: datetime | None
