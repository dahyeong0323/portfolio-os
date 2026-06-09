from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from portfolio_os.db.connection import Database


def utc_now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "migrations"


def initialize_database(db_path: Path, migrations_dir: Path | None = None) -> None:
    migrations_root = migrations_dir or default_migrations_dir()
    db = Database(db_path)
    db.connect()
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL
            )
            """
        )
        db.commit()
        for migration_path in sorted(migrations_root.glob("*.sql")):
            version_text, name = migration_path.name.split("_", 1)
            version = int(version_text)
            sql = migration_path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            existing = db.fetch_one("SELECT checksum FROM schema_migrations WHERE version = ?", (version,))
            if existing is not None:
                if existing["checksum"] != checksum:
                    raise RuntimeError(f"Migration checksum mismatch: {migration_path.name}")
                continue
            db.executescript(sql)
            db.execute(
                "INSERT INTO schema_migrations(version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                (version, name, utc_now_text(), checksum),
            )
            db.commit()
    finally:
        db.close()
