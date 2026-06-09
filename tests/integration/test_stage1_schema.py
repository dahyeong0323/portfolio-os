from __future__ import annotations


def test_schema_migrations_and_core_tables_exist(db) -> None:
    tables = {row["name"] for row in db.fetch_all("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "schema_migrations" in tables
    for table in {
        "accounts",
        "instruments",
        "transactions",
        "cash_balances",
        "liabilities",
        "tax_reserves",
        "reconciliation_snapshots",
    }:
        assert table in tables
    assert db.fetch_one("PRAGMA foreign_keys")["foreign_keys"] == 1
