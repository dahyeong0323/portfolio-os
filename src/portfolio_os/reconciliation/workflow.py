from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from portfolio_os.db import Database
from portfolio_os.importers import load_external_snapshot
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ReconciliationResult
from portfolio_os.reconciliation.report_writer import ReconciliationReportWriter
from portfolio_os.reconciliation.service import DEFAULT_TOLERANCE, ReconciliationService
from portfolio_os.repositories import (
    CashBalanceRepository,
    ReconciliationRepository,
    TransactionRepository,
)


@dataclass(frozen=True)
class ReconciliationWorkflowOutcome:
    reconciliation: ReconciliationResult
    markdown_report: Path | None
    json_report: Path | None
    warnings: tuple[str, ...]


class ReconciliationWorkflowService:
    """Orchestrates the existing ledger, reconciliation, repository, and report boundaries."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def run_from_artifact(
        self,
        artifact_path: Path,
        account_id: int | None,
        report_dir: Path,
    ) -> ReconciliationWorkflowOutcome:
        return self.run(load_external_snapshot(artifact_path), account_id, report_dir)

    def run(
        self,
        external_snapshot: ExternalAccountSnapshot,
        account_id: int | None,
        report_dir: Path,
    ) -> ReconciliationWorkflowOutcome:
        ledger = LedgerSnapshotBuilder(self.db).build_snapshot(external_snapshot.as_of_date, account_id)
        result = ReconciliationService().run_reconciliation(
            ledger,
            external_snapshot,
            DEFAULT_TOLERANCE,
            account_id=account_id,
        )
        saved = ReconciliationRepository(self.db).save_reconciliation_result(result)

        if saved.reconciliation_status == "passed":
            transaction_repo = TransactionRepository(self.db)
            transaction_ids = [
                transaction.transaction_id
                for transaction in transaction_repo.list_unconfirmed_transactions(
                    account_id,
                    through_date=external_snapshot.as_of_date,
                )
            ]
            transaction_repo.mark_transactions_confirmed(transaction_ids)

            cash_repo = CashBalanceRepository(self.db)
            cash_ids = [
                balance.cash_balance_id
                for balance in cash_repo.list_cash_balances(account_id, external_snapshot.as_of_date)
                if not balance.is_reconciled
            ]
            cash_repo.mark_cash_balances_reconciled(cash_ids)

        warnings: list[str] = []
        markdown_path: Path | None = None
        json_path: Path | None = None
        try:
            writer = ReconciliationReportWriter()
            markdown_path = report_dir / f"reconciliation_{saved.reconciliation_id}.md"
            json_path = report_dir / f"reconciliation_{saved.reconciliation_id}.json"
            writer.write_markdown_report(saved, markdown_path)
            writer.write_json_report(saved, json_path)
        except OSError:
            warnings.append("The reconciliation was saved, but its report files could not be generated.")
            markdown_path = None
            json_path = None

        return ReconciliationWorkflowOutcome(saved, markdown_path, json_path, tuple(warnings))
