from __future__ import annotations

from datetime import date, datetime, timedelta

from portfolio_os.db.connection import Database
from portfolio_os.models import LedgerStatus, ReconciliationStatus
from portfolio_os.repositories import ReconciliationRepository
from portfolio_os.validators import date_to_text, datetime_from_text, utc_now

STALE_AFTER_DAYS = 7


class LedgerStateMachine:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db

    def get_current_status(self, account_id: int | None = None, as_of_date: date | None = None) -> LedgerStatus:
        if self.db is None:
            return "provisional"
        latest = ReconciliationRepository(self.db).get_latest_reconciliation(account_id)
        if latest is None:
            return "provisional"
        completed_at_text = latest["completed_at"]
        latest_after = latest["ledger_status_after"]
        if completed_at_text is None:
            return "provisional"
        completed_at = datetime_from_text(completed_at_text)
        if latest_after == "broken":
            if self._has_correction_after(completed_at, account_id):
                return "provisional"
            return "broken"
        if self._has_any_input_after(completed_at, account_id, as_of_date):
            return "provisional"
        return self.mark_stale_if_needed(latest_after, completed_at, utc_now(), STALE_AFTER_DAYS)

    def determine_next_status_after_input(self, previous_status: LedgerStatus, transaction_type: str | None = None) -> LedgerStatus:
        if previous_status == "broken" and transaction_type not in {"reversal", "correction"}:
            return "broken"
        return "provisional"

    def determine_next_status_after_reconciliation(
        self,
        previous_status: LedgerStatus,
        reconciliation_status: ReconciliationStatus,
        has_unresolved_differences: bool,
    ) -> LedgerStatus:
        if reconciliation_status == "passed" and not has_unresolved_differences:
            return "reconciled"
        if reconciliation_status == "failed":
            return "broken"
        if reconciliation_status == "needs_review" and has_unresolved_differences:
            return "broken"
        return "provisional"

    def mark_stale_if_needed(
        self,
        current_status: LedgerStatus,
        last_reconciled_at: datetime | None,
        now: datetime,
        stale_after_days: int,
    ) -> LedgerStatus:
        if current_status == "broken":
            return "broken"
        if last_reconciled_at is None:
            return "provisional"
        if now - last_reconciled_at > timedelta(days=stale_after_days):
            return "stale"
        return current_status

    def _has_correction_after(self, completed_at: datetime, account_id: int | None) -> bool:
        del completed_at
        sql = "SELECT 1 FROM transactions WHERE is_confirmed = 0 AND transaction_type IN ('reversal','correction')"
        params: list[object] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        sql += " LIMIT 1"
        assert self.db is not None
        return self.db.fetch_one(sql, params) is not None

    def _has_any_input_after(self, completed_at: datetime, account_id: int | None, as_of_date: date | None) -> bool:
        completed = completed_at.isoformat().replace("+00:00", "Z")
        date_filter = date_to_text(as_of_date) if as_of_date else None
        assert self.db is not None
        transaction_sql = "SELECT 1 FROM transactions WHERE is_confirmed = 0"
        transaction_params: list[object] = []
        if account_id is not None:
            transaction_sql += " AND account_id = ?"
            transaction_params.append(account_id)
        if date_filter is not None:
            transaction_sql += " AND trade_date <= ?"
            transaction_params.append(date_filter)
        if self.db.fetch_one(transaction_sql + " LIMIT 1", transaction_params) is not None:
            return True

        cash_sql = "SELECT 1 FROM cash_balances WHERE is_reconciled = 0"
        cash_params: list[object] = []
        if account_id is not None:
            cash_sql += " AND account_id = ?"
            cash_params.append(account_id)
        if date_filter is not None:
            cash_sql += " AND as_of_date <= ?"
            cash_params.append(date_filter)
        if self.db.fetch_one(cash_sql + " LIMIT 1", cash_params) is not None:
            return True

        for table, account_col, date_col in [("liabilities", "account_id", "as_of_date"), ("tax_reserves", "account_id", "as_of_date")]:
            sql = f"SELECT 1 FROM {table} WHERE created_at > ?"
            params: list[object] = [completed]
            if account_id is not None:
                sql += f" AND {account_col} = ?"
                params.append(account_id)
            if date_filter is not None:
                sql += f" AND {date_col} <= ?"
                params.append(date_filter)
            if self.db.fetch_one(sql + " LIMIT 1", params) is not None:
                return True
        return False
