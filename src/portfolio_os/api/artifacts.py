from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from portfolio_os.api.errors import ApiError
from portfolio_os.validators import datetime_from_text, datetime_to_text


@dataclass(frozen=True)
class ExternalSnapshotArtifactMetadata:
    artifact_id: str
    account_id: int
    source: str
    as_of_date: date
    imported_at: datetime
    snapshot_filename: str


def normalize_artifact_id(artifact_id: str) -> str:
    try:
        parsed = UUID(artifact_id)
    except ValueError as exc:
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.") from exc
    if str(parsed) != artifact_id.lower():
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.")
    return str(parsed)


def artifact_directory(root: Path, artifact_id: str) -> Path:
    normalized = normalize_artifact_id(artifact_id)
    root_resolved = root.resolve()
    candidate = (root_resolved / normalized).resolve()
    if candidate.parent != root_resolved:
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.")
    return candidate


def write_artifact_metadata(directory: Path, metadata: ExternalSnapshotArtifactMetadata) -> None:
    payload = asdict(metadata)
    payload["as_of_date"] = metadata.as_of_date.isoformat()
    payload["imported_at"] = datetime_to_text(metadata.imported_at)
    (directory / "metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_artifact_metadata(root: Path, artifact_id: str) -> ExternalSnapshotArtifactMetadata:
    directory = artifact_directory(root, artifact_id)
    metadata_path = directory / "metadata.json"
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata = ExternalSnapshotArtifactMetadata(
            artifact_id=str(payload["artifact_id"]),
            account_id=int(payload["account_id"]),
            source=str(payload["source"]),
            as_of_date=date.fromisoformat(payload["as_of_date"]),
            imported_at=datetime_from_text(payload["imported_at"]),
            snapshot_filename=str(payload["snapshot_filename"]),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.") from exc
    if metadata.artifact_id != normalize_artifact_id(artifact_id):
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.")
    return metadata


def resolve_snapshot_artifact(root: Path, artifact_id: str) -> tuple[ExternalSnapshotArtifactMetadata, Path]:
    metadata = load_artifact_metadata(root, artifact_id)
    directory = artifact_directory(root, artifact_id)
    snapshot_path = (directory / metadata.snapshot_filename).resolve()
    if snapshot_path.parent != directory.resolve() or not snapshot_path.is_file():
        raise ApiError(404, "snapshot_artifact_not_found", "The external snapshot artifact was not found.")
    return metadata, snapshot_path


def report_path(root: Path, reconciliation_id: int, suffix: str = "md") -> Path:
    if reconciliation_id <= 0 or suffix not in {"md", "json"}:
        raise ApiError(404, "reconciliation_report_not_found", "The reconciliation report was not found.")
    root_resolved = root.resolve()
    candidate = (root_resolved / f"reconciliation_{reconciliation_id}.{suffix}").resolve()
    if candidate.parent != root_resolved:
        raise ApiError(404, "reconciliation_report_not_found", "The reconciliation report was not found.")
    return candidate
