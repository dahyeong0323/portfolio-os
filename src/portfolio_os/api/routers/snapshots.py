from __future__ import annotations

import csv
import shutil
import tempfile
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from portfolio_os.api.artifacts import ExternalSnapshotArtifactMetadata, write_artifact_metadata
from portfolio_os.api.deps import get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.snapshots import ExternalSnapshotImportResponse
from portfolio_os.db import Database
from portfolio_os.importers import AccountSnapshotCSVImporter, CSVImportError, write_external_snapshot
from portfolio_os.repositories import AccountRepository, InstrumentRepository
from portfolio_os.validators import utc_now

router = APIRouter(prefix="/snapshots", tags=["external snapshots"])

CSV_HEADERS = {
    "positions": {"symbol", "currency", "quantity"},
    "cash": {"currency", "amount"},
    "liabilities": {"liability_name", "currency", "current_amount"},
    "tax_reserves": {"tax_year", "tax_type", "currency", "reserved_amount"},
}
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",
    "text/plain",
}


async def _store_csv(upload: UploadFile, destination: Path, limit_bytes: int, kind: str) -> Path:
    filename = upload.filename or ""
    if Path(filename).suffix.lower() != ".csv":
        raise ApiError(422, "invalid_snapshot_file", f"The {kind} upload must be a CSV file.")
    if upload.content_type and upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise ApiError(422, "invalid_snapshot_file", f"The {kind} upload has an unsupported content type.")

    total = 0
    try:
        with destination.open("wb") as handle:
            while chunk := await upload.read(64 * 1024):
                total += len(chunk)
                if total > limit_bytes:
                    raise ApiError(413, "snapshot_file_too_large", f"The {kind} CSV exceeds the upload limit.")
                handle.write(chunk)
    finally:
        await upload.close()

    try:
        with destination.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = {header.strip() for header in (reader.fieldnames or []) if header}
    except UnicodeDecodeError as exc:
        raise ApiError(422, "invalid_snapshot_encoding", f"The {kind} CSV must be UTF-8 encoded.") from exc
    missing = sorted(CSV_HEADERS[kind] - headers)
    if missing:
        raise ApiError(
            422,
            "invalid_snapshot_headers",
            f"The {kind} CSV is missing required headers.",
            {"missing": missing},
        )
    return destination


@router.post(
    "/external-imports",
    response_model=ExternalSnapshotImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_external_snapshot(
    request: Request,
    account_id: int = Form(..., gt=0),
    as_of_date: date = Form(...),
    positions_file: UploadFile | None = File(None),
    cash_file: UploadFile | None = File(None),
    liabilities_file: UploadFile | None = File(None),
    tax_reserves_file: UploadFile | None = File(None),
    db: Database = Depends(get_writable_database),
) -> ExternalSnapshotImportResponse:
    uploads = {
        "positions": positions_file,
        "cash": cash_file,
        "liabilities": liabilities_file,
        "tax_reserves": tax_reserves_file,
    }
    if not any(uploads.values()):
        raise ApiError(422, "snapshot_files_required", "At least one external snapshot CSV is required.")
    if AccountRepository(db).get_account(account_id) is None:
        raise ApiError(404, "account_not_found", "The selected account was not found.")

    snapshot_root = Path(request.app.state.snapshot_dir)
    snapshot_root.mkdir(parents=True, exist_ok=True)
    artifact_id = str(uuid4())
    artifact_dir = snapshot_root / artifact_id

    try:
        with tempfile.TemporaryDirectory(prefix=".upload-", dir=snapshot_root) as temp_name:
            temp_dir = Path(temp_name)
            paths: dict[str, Path] = {}
            for kind, upload in uploads.items():
                if upload is not None:
                    paths[kind] = await _store_csv(
                        upload,
                        temp_dir / f"{kind}.csv",
                        int(request.app.state.upload_limit_bytes),
                        kind,
                    )

            importer = AccountSnapshotCSVImporter(InstrumentRepository(db))
            positions = importer.parse_positions_csv(paths["positions"], account_id, as_of_date) if "positions" in paths else ()
            cash = importer.parse_cash_csv(paths["cash"], account_id, as_of_date) if "cash" in paths else ()
            liabilities = importer.parse_liabilities_csv(paths["liabilities"], as_of_date) if "liabilities" in paths else ()
            tax_reserves = importer.parse_tax_reserves_csv(paths["tax_reserves"], as_of_date) if "tax_reserves" in paths else ()

            for item in (*liabilities, *tax_reserves):
                if item.account_id not in {None, account_id}:
                    raise ApiError(
                        422,
                        "snapshot_account_mismatch",
                        "External snapshot rows may only reference the selected account.",
                    )
            if not any((positions, cash, liabilities, tax_reserves)):
                raise ApiError(422, "external_snapshot_empty", "The uploaded CSV files contain no snapshot rows.")

            snapshot = importer.build_external_snapshot(
                as_of_date,
                "csv_import",
                positions,
                cash,
                liabilities,
                tax_reserves,
            )
            artifact_dir.mkdir(parents=False, exist_ok=False)
            snapshot_path = write_external_snapshot(snapshot, artifact_dir)
            metadata = ExternalSnapshotArtifactMetadata(
                artifact_id=artifact_id,
                account_id=account_id,
                source="csv_import",
                as_of_date=as_of_date,
                imported_at=snapshot.received_at,
                snapshot_filename=snapshot_path.name,
            )
            write_artifact_metadata(artifact_dir, metadata)
    except ApiError:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise
    except (CSVImportError, UnicodeDecodeError, ValueError) as exc:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise ApiError(422, "snapshot_import_failed", "The external snapshot CSV could not be imported.", str(exc)) from exc
    except OSError as exc:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise ApiError(500, "snapshot_storage_error", "The external snapshot artifact could not be stored.") from exc

    warnings = [
        f"{position.symbol}: {position.match_error or position.match_status}"
        for position in positions
        if position.match_status != "matched"
    ]
    return ExternalSnapshotImportResponse(
        artifact_id=artifact_id,
        account_id=account_id,
        source="csv_import",
        as_of_date=as_of_date,
        status="imported_with_warnings" if warnings else "imported",
        counts={
            "positions": len(positions),
            "cash": len(cash),
            "liabilities": len(liabilities),
            "tax_reserves": len(tax_reserves),
        },
        warnings=warnings,
        imported_at=metadata.imported_at,
    )
