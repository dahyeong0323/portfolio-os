from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

from portfolio_os.models import (
    CashDifference,
    ExternalAccountSnapshot,
    ExternalCash,
    ExternalLiability,
    ExternalPosition,
    ExternalTaxReserve,
    LedgerCash,
    LedgerLiability,
    LedgerPosition,
    LedgerSnapshot,
    LedgerTaxReserve,
    PositionDifference,
    ReconciliationResult,
    ReconciliationTolerance,
    TaxReserveDifference,
    LiabilityDifference,
)

DEFAULT_TOLERANCE = ReconciliationTolerance(
    cash_abs=Decimal("1.00"),
    quantity_abs=Decimal("0.000001"),
    liability_abs=Decimal("1.00"),
    tax_reserve_abs=Decimal("1.00"),
)


class ReconciliationService:
    def run_reconciliation(
        self,
        ledger_snapshot: LedgerSnapshot,
        external_snapshot: ExternalAccountSnapshot,
        tolerance: ReconciliationTolerance = DEFAULT_TOLERANCE,
        account_id: int | None = None,
    ) -> ReconciliationResult:
        started_at = datetime.now(timezone.utc).replace(microsecond=0)
        position_diffs = self.compare_positions(ledger_snapshot.positions, external_snapshot.positions, tolerance.quantity_abs)
        cash_diffs = self.compare_cash(ledger_snapshot.cash, external_snapshot.cash, tolerance.cash_abs)
        liability_diffs = self.compare_liabilities(ledger_snapshot.liabilities, external_snapshot.liabilities, tolerance.liability_abs)
        tax_diffs = self.compare_tax_reserves(ledger_snapshot.tax_reserves, external_snapshot.tax_reserves, tolerance.tax_reserve_abs)
        unresolved_positions = [p for p in external_snapshot.positions if p.match_status != "matched"]
        over_tolerance = [
            *(diff for diff in position_diffs if not diff.within_tolerance),
            *(diff for diff in cash_diffs if not diff.within_tolerance),
            *(diff for diff in liability_diffs if not diff.within_tolerance),
            *(diff for diff in tax_diffs if not diff.within_tolerance),
        ]
        if unresolved_positions:
            status = "needs_review"
            ledger_after = "broken"
            failure_reason = "; ".join(p.match_error or f"unresolved instrument: {p.symbol}" for p in unresolved_positions)
        elif over_tolerance:
            status = "failed"
            ledger_after = "broken"
            failure_reason = "one or more reconciliation differences exceed tolerance"
        else:
            status = "passed"
            ledger_after = "reconciled"
            failure_reason = None
        completed_at = datetime.now(timezone.utc).replace(microsecond=0)
        return ReconciliationResult(
            reconciliation_id=None,
            account_id=account_id,
            as_of_date=ledger_snapshot.as_of_date,
            started_at=started_at,
            completed_at=completed_at,
            ledger_status_before=ledger_snapshot.ledger_status,
            ledger_status_after=ledger_after,
            reconciliation_status=status,
            snapshot_source=external_snapshot.source,
            expected_positions=ledger_snapshot.positions,
            actual_positions=external_snapshot.positions,
            position_differences=position_diffs,
            expected_cash=ledger_snapshot.cash,
            actual_cash=external_snapshot.cash,
            cash_differences=cash_diffs,
            expected_liabilities=ledger_snapshot.liabilities,
            actual_liabilities=external_snapshot.liabilities,
            liability_differences=liability_diffs,
            expected_tax_reserves=ledger_snapshot.tax_reserves,
            actual_tax_reserves=external_snapshot.tax_reserves,
            tax_reserve_differences=tax_diffs,
            tolerance=tolerance,
            failure_reason=failure_reason,
        )

    def compare_positions(
        self,
        expected: Sequence[LedgerPosition],
        actual: Sequence[ExternalPosition],
        tolerance: Decimal,
    ) -> tuple[PositionDifference, ...]:
        expected_by_key = {(item.account_id, item.instrument_id): item for item in expected}
        actual_by_key = {(item.account_id, item.instrument_id): item for item in actual if item.instrument_id is not None}
        keys = set(expected_by_key) | set(actual_by_key)
        diffs: list[PositionDifference] = []
        for key in sorted(keys):
            expected_item = expected_by_key.get(key)
            actual_item = actual_by_key.get(key)
            expected_qty = expected_item.quantity if expected_item else Decimal("0")
            actual_qty = actual_item.quantity if actual_item else Decimal("0")
            diff = actual_qty - expected_qty
            if diff == 0:
                continue
            symbol = expected_item.symbol if expected_item else actual_item.symbol  # type: ignore[union-attr]
            diffs.append(PositionDifference(key[0], key[1], symbol, expected_qty, actual_qty, diff, abs(diff) <= tolerance))
        for actual_item in actual:
            if actual_item.instrument_id is None:
                diffs.append(
                    PositionDifference(
                        actual_item.account_id,
                        None,
                        actual_item.symbol,
                        Decimal("0"),
                        actual_item.quantity,
                        actual_item.quantity,
                        False,
                    )
                )
        return tuple(diffs)

    def compare_cash(self, expected: Sequence[LedgerCash], actual: Sequence[ExternalCash], tolerance: Decimal) -> tuple[CashDifference, ...]:
        expected_by_key = {(item.account_id, item.currency): item for item in expected}
        actual_by_key = {(item.account_id, item.currency): item for item in actual}
        diffs: list[CashDifference] = []
        for key in sorted(set(expected_by_key) | set(actual_by_key)):
            expected_amount = expected_by_key[key].amount if key in expected_by_key else Decimal("0")
            actual_amount = actual_by_key[key].amount if key in actual_by_key else Decimal("0")
            diff = actual_amount - expected_amount
            if diff != 0:
                diffs.append(CashDifference(key[0], key[1], expected_amount, actual_amount, diff, abs(diff) <= tolerance))
        return tuple(diffs)

    def compare_liabilities(
        self,
        expected: Sequence[LedgerLiability],
        actual: Sequence[ExternalLiability],
        tolerance: Decimal,
    ) -> tuple[LiabilityDifference, ...]:
        expected_by_key = {(item.account_id, item.liability_name, item.currency): item for item in expected}
        actual_by_key = {(item.account_id, item.liability_name, item.currency): item for item in actual}
        diffs: list[LiabilityDifference] = []
        for key in sorted(set(expected_by_key) | set(actual_by_key), key=lambda item: (item[0] or 0, item[1], item[2])):
            expected_amount = expected_by_key[key].current_amount if key in expected_by_key else Decimal("0")
            actual_amount = actual_by_key[key].current_amount if key in actual_by_key else Decimal("0")
            diff = actual_amount - expected_amount
            if diff != 0:
                diffs.append(LiabilityDifference(key[0], key[1], key[2], expected_amount, actual_amount, diff, abs(diff) <= tolerance))
        return tuple(diffs)

    def compare_tax_reserves(
        self,
        expected: Sequence[LedgerTaxReserve],
        actual: Sequence[ExternalTaxReserve],
        tolerance: Decimal,
    ) -> tuple[TaxReserveDifference, ...]:
        expected_by_key = {(item.account_id, item.tax_year, item.tax_type, item.currency): item for item in expected}
        actual_by_key = {(item.account_id, item.tax_year, item.tax_type, item.currency): item for item in actual}
        diffs: list[TaxReserveDifference] = []
        for key in sorted(set(expected_by_key) | set(actual_by_key), key=lambda item: (item[0] or 0, item[1], item[2], item[3])):
            expected_amount = expected_by_key[key].reserved_amount if key in expected_by_key else Decimal("0")
            actual_amount = actual_by_key[key].reserved_amount if key in actual_by_key else Decimal("0")
            diff = actual_amount - expected_amount
            if diff != 0:
                diffs.append(TaxReserveDifference(key[0], key[1], key[2], key[3], expected_amount, actual_amount, diff, abs(diff) <= tolerance))
        return tuple(diffs)
