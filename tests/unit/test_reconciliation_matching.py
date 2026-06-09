from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio_os.importers.csv_snapshot_importer import AccountSnapshotCSVImporter
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ExternalPosition, LedgerSnapshot
from portfolio_os.reconciliation import ReconciliationService
from portfolio_os.repositories import InstrumentRepository
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_cash_anchor, seed_instrument


def test_ambiguous_symbol_matching_becomes_needs_review_broken(db, tmp_path) -> None:
    account_id = seed_account(db)
    seed_instrument(db, "ABC", "NYSE")
    seed_instrument(db, "ABC", "NASDAQ")
    csv_path = tmp_path / "positions.csv"
    csv_path.write_text("symbol,currency,quantity\nABC,USD,1\n", encoding="utf-8")

    importer = AccountSnapshotCSVImporter(InstrumentRepository(db))
    positions = importer.parse_positions_csv(csv_path, account_id, date(2026, 1, 2))
    assert positions[0].match_status == "ambiguous"

    seed_cash_anchor(db, account_id)
    ledger = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id)
    snapshot = ExternalAccountSnapshot(date(2026, 1, 2), "csv_import", positions, (), (), (), utc_now())
    result = ReconciliationService().run_reconciliation(ledger, snapshot, account_id=account_id)
    assert result.reconciliation_status == "needs_review"
    assert result.ledger_status_after == "broken"


def test_unresolved_position_diff_is_not_silently_passed() -> None:
    snapshot = ExternalAccountSnapshot(
        date(2026, 1, 2),
        "csv_import",
        (ExternalPosition(1, "MISSING", "USD", Decimal("1"), match_status="missing", match_error="missing"),),
        (),
        (),
        (),
        utc_now(),
    )
    result = ReconciliationService().run_reconciliation(
        ledger_snapshot=LedgerSnapshot(date(2026, 1, 2), "provisional", (), (), (), (), utc_now()),
        external_snapshot=snapshot,
    )
    assert result.reconciliation_status != "passed"
