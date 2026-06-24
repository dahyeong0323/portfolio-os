from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Sequence

from portfolio_os.db.pragmas import apply_pragmas, apply_read_only_pragmas


class Database:
    def __init__(self, db_path: Path, *, read_only: bool = False) -> None:
        self.db_path = Path(db_path)
        self.read_only = read_only
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        if self.read_only:
            uri = f"{self.db_path.resolve().as_uri()}?mode=ro"
            self.connection = sqlite3.connect(uri, uri=True)
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        if self.read_only:
            apply_read_only_pragmas(self.connection)
        else:
            apply_pragmas(self.connection)

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _conn(self) -> sqlite3.Connection:
        if self.connection is None:
            self.connect()
        assert self.connection is not None
        return self.connection

    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        return self._conn().execute(sql, params)

    def executescript(self, sql: str) -> None:
        self._conn().executescript(sql)

    def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        row = self.execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return [dict(row) for row in self.execute(sql, params).fetchall()]

    def begin(self) -> None:
        self.execute("BEGIN")

    def commit(self) -> None:
        self._conn().commit()

    def rollback(self) -> None:
        self._conn().rollback()

    def __enter__(self) -> Database:
        self.connect()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
