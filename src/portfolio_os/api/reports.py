from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from portfolio_os.api.errors import ApiError


REPORT_ACTIONS = ["view", "copy", "download"]
BLOCKED_REPORT_ACTIONS = [
    "create_order",
    "approve",
    "reject",
    "execute",
    "confirm",
    "mutate_ledger",
    "broker_write",
]
FORMAT_SUFFIXES = {"markdown": ".md", "json": ".json"}
SUFFIX_FORMATS = {value: key for key, value in FORMAT_SUFFIXES.items()}


@dataclass(frozen=True)
class ReportCategoryConfig:
    category_id: str
    label: str
    description: str
    directory: Path
    filename_prefix: str
    linked_object_type: str | None
    supported_formats: tuple[str, ...] = ("markdown", "json")


@dataclass(frozen=True)
class ReportRecord:
    report_reference: str
    category: str
    title: str
    format: str
    generated_at: datetime
    linked_object_type: str | None
    linked_object_id: str | None
    safe_summary: str | None
    available_actions: list[str]
    blocked_actions: list[str]
    filename: str
    path: Path


def _reference(category_id: str, filename: str) -> str:
    payload = json.dumps({"c": category_id, "f": filename}, separators=(",", ":"), sort_keys=True)
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    return f"report_{encoded}"


def _decode_reference(report_reference: str) -> tuple[str, str]:
    if not report_reference.startswith("report_"):
        raise ApiError(404, "report_not_found", "The report was not found.")
    encoded = report_reference.removeprefix("report_")
    try:
        padding = "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode((encoded + padding).encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(404, "report_not_found", "The report was not found.") from exc
    category = payload.get("c")
    filename = payload.get("f")
    if not isinstance(category, str) or not isinstance(filename, str):
        raise ApiError(404, "report_not_found", "The report was not found.")
    return category, filename


def _safe_filename(filename: str) -> str:
    if filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise ApiError(404, "report_not_found", "The report was not found.")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUFFIX_FORMATS:
        raise ApiError(422, "unsupported_report_format", "Only Markdown and JSON reports are supported.")
    return filename


def _object_id(filename: str, prefix: str) -> str | None:
    stem = Path(filename).stem
    if not stem.startswith(prefix):
        return None
    value = stem.removeprefix(prefix)
    return value if re.fullmatch(r"[0-9A-Za-z_-]+", value) else None


def _title(category: ReportCategoryConfig, filename: str) -> str:
    linked_id = _object_id(filename, category.filename_prefix)
    if linked_id:
        return f"{category.label} #{linked_id}"
    return Path(filename).stem.replace("_", " ").title()


def _summary(path: Path, report_format: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if report_format == "json":
        return "JSON report artifact"
    for line in text.splitlines():
        cleaned = line.strip().lstrip("#").strip()
        if cleaned:
            return cleaned[:240]
    return None


class ReportRegistry:
    def __init__(self, report_dir: Path, repo_root: Path | None = None) -> None:
        self.report_dir = report_dir
        self.repo_root = repo_root or Path.cwd()
        self.configs = self._configs()

    def _exports_root(self) -> Path:
        if self.report_dir.name == "reconciliation_reports":
            return self.report_dir.parent
        return self.repo_root / "data" / "exports"

    def _configs(self) -> dict[str, ReportCategoryConfig]:
        exports = self._exports_root()
        configs = [
            ReportCategoryConfig("reconciliation", "정산 리포트", "Generated reconciliation Markdown and JSON reports.", self.report_dir, "reconciliation_", "reconciliation"),
            ReportCategoryConfig("risk_validation", "리스크 리포트", "Risk Engine validation reports.", exports / "risk_reports", "risk_validation_", "risk_validation"),
            ReportCategoryConfig("order_ticket", "주문 티켓 리포트", "Order ticket audit reports. These are not execution authority.", exports / "order_tickets", "order_ticket_", "order_ticket"),
            ReportCategoryConfig("senior_memo", "시니어 메모", "Senior decision memo reports.", exports / "senior_memos", "senior_memo_", "senior_memo"),
            ReportCategoryConfig("research", "리서치 리포트", "Sourced research packet reports.", exports / "research_reports", "research_packet_", "research_packet"),
            ReportCategoryConfig("macro", "매크로 리포트", "Macro context packet reports.", exports / "macro_reports", "macro_context_", "macro_context_packet"),
            ReportCategoryConfig("governance", "거버넌스", "Governance policy reports.", exports / "governance_reports", "governance_policy_", "governance_policy"),
            ReportCategoryConfig("canary", "카나리 리포트", "Canary run reports.", exports / "canary_reports", "canary_run_", "canary_run"),
            ReportCategoryConfig("context_package", "컨텍스트 패키지", "Context package reports.", exports / "context_packages", "context_package_", "context_package"),
            ReportCategoryConfig("health", "헬스 리포트", "System health reports.", exports / "health_reports", "system_health_", "system_health_snapshot"),
            ReportCategoryConfig("frontend_stage", "개발 리포트", "Safe frontend stage implementation, handoff, and API contract documents.", self.repo_root / "docs" / "frontend", "stage", "frontend_stage", ("markdown",)),
        ]
        return {config.category_id: config for config in configs}

    def _files(self, config: ReportCategoryConfig) -> list[Path]:
        if not config.directory.is_dir():
            return []
        suffixes = {FORMAT_SUFFIXES[item] for item in config.supported_formats}
        files: list[Path] = []
        for path in config.directory.iterdir():
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if config.category_id == "frontend_stage":
                if not (path.name.startswith("stage") and path.suffix.lower() == ".md"):
                    continue
            elif not path.name.startswith(config.filename_prefix):
                continue
            files.append(path)
        return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)

    def categories(self) -> list[dict]:
        categories: list[dict] = []
        for config in self.configs.values():
            records = self._files(config)
            latest = max((path.stat().st_mtime for path in records), default=None)
            categories.append(
                {
                    "category_id": config.category_id,
                    "label": config.label,
                    "description": config.description,
                    "report_count": len(records),
                    "supported_formats": list(config.supported_formats),
                    "latest_generated_at": datetime.fromtimestamp(latest, tz=timezone.utc) if latest else None,
                }
            )
        return categories

    def list_reports(
        self,
        category: str | None = None,
        report_format: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, list[ReportRecord]]:
        if report_format is not None and report_format not in FORMAT_SUFFIXES:
            raise ApiError(422, "unsupported_report_format", "Only Markdown and JSON reports are supported.")
        configs = list(self.configs.values())
        if category:
            config = self.configs.get(category)
            if config is None:
                raise ApiError(422, "unsupported_report_category", "The report category is not supported.")
            configs = [config]
        records: list[ReportRecord] = []
        for config in configs:
            records.extend(self._record(config, path) for path in self._files(config))
        if report_format:
            records = [record for record in records if record.format == report_format]
        records.sort(key=lambda item: item.generated_at, reverse=True)
        safe_offset = max(0, offset)
        safe_limit = max(1, min(limit, 200))
        return len(records), records[safe_offset : safe_offset + safe_limit]

    def get_report(self, report_reference: str) -> ReportRecord:
        category_id, filename = _decode_reference(report_reference)
        config = self.configs.get(category_id)
        if config is None:
            raise ApiError(404, "report_not_found", "The report was not found.")
        filename = _safe_filename(filename)
        root = config.directory.resolve()
        candidate = (root / filename).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ApiError(404, "report_not_found", "The report was not found.") from exc
        if candidate not in [path.resolve() for path in self._files(config)]:
            raise ApiError(404, "report_not_found", "The report was not found.")
        return self._record(config, candidate)

    def _record(self, config: ReportCategoryConfig, path: Path) -> ReportRecord:
        suffix = path.suffix.lower()
        report_format = SUFFIX_FORMATS.get(suffix)
        if report_format is None:
            raise ApiError(422, "unsupported_report_format", "Only Markdown and JSON reports are supported.")
        linked_id = _object_id(path.name, config.filename_prefix)
        return ReportRecord(
            report_reference=_reference(config.category_id, path.name),
            category=config.category_id,
            title=_title(config, path.name),
            format=report_format,
            generated_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
            linked_object_type=config.linked_object_type if linked_id else None,
            linked_object_id=linked_id,
            safe_summary=_summary(path, report_format),
            available_actions=list(REPORT_ACTIONS),
            blocked_actions=list(BLOCKED_REPORT_ACTIONS),
            filename=path.name,
            path=path,
        )
