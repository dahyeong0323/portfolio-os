import { useSyncExternalStore } from "react";
import { apiRuntime } from "../../api/client";
import { useConfirmExecutionsAfterReconciliation, useExecutionsQuery } from "../../api/queries/executions";
import { useReconciliationQuery } from "../../api/queries/reconciliation";
import type { PendingExecution } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { formatDate, formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function reasonLabel(reason: string | null): string {
  const labels: Record<string, string> = {
    transaction_not_confirmed: "연결 거래가 아직 정산으로 confirmed 처리되지 않았습니다.",
    reconciliation_not_available: "사용 가능한 정산 증거가 없습니다.",
    reconciliation_not_passed: "passed 정산 증거가 아닙니다.",
    execution_after_reconciliation: "실행 시각이 정산 기준일보다 늦습니다.",
    override_execution_deferred: "오버라이드 실행 확정은 후속 단계입니다.",
    missing_provisional_transaction: "연결된 provisional transaction이 없습니다.",
    provisional_transaction_not_found: "연결된 transaction을 찾을 수 없습니다.",
    execution_not_pending: "이미 pending 상태가 아닙니다.",
    reconciliation_account_mismatch: "정산 계좌 범위와 실행 계좌가 다릅니다.",
  };
  return reason ? labels[reason] ?? reason : "확정 가능";
}

export function PendingExecutionsPage() {
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const mockMode = runtime.source === "mock";
  const executions = useExecutionsQuery();
  const reconciliation = useReconciliationQuery();
  const confirm = useConfirmExecutionsAfterReconciliation();
  const latest = reconciliation.data?.reconciliation;

  const columns: DataColumn<PendingExecution>[] = [
    { key: "id", header: "실행 ID", render: (row) => <span className="mono">#{row.manual_execution_id}</span> },
    {
      key: "ticket",
      header: "연결 티켓",
      render: (row) => (row.linked_ticket ? <span className="mono">#TKT-{row.linked_ticket.order_ticket_id}</span> : "-"),
    },
    {
      key: "tx",
      header: "Provisional TX",
      render: (row) => (row.created_transaction_id ? <span className="mono">#{row.created_transaction_id}</span> : "-"),
    },
    {
      key: "amount",
      header: "체결",
      render: (row) => `${formatDecimal(row.executed_quantity)} @ ${formatMoney(row.executed_price, row.currency)}`,
    },
    { key: "time", header: "실행 시각", render: (row) => formatDateTime(row.executed_at) },
    {
      key: "txConfirmed",
      header: "거래 확인",
      render: (row) => (
        <StatusBadge
          label={row.transaction_is_confirmed ? "confirmed" : "pending"}
          tone={row.transaction_is_confirmed ? "green" : "amber"}
        />
      ),
    },
    {
      key: "evidence",
      header: "정산 증거",
      render: (row) =>
        row.reconciliation_evidence
          ? `${row.reconciliation_evidence.reconciliation_status} · ${formatDate(row.reconciliation_evidence.as_of_date)}`
          : "없음",
    },
    {
      key: "eligibility",
      header: "확정 가능",
      render: (row) => (
        <StatusBadge
          label={row.confirmation_eligible ? "가능" : "대기"}
          tone={row.confirmation_eligible ? "green" : "amber"}
          title={reasonLabel(row.confirmation_blocked_reason)}
        />
      ),
    },
    {
      key: "action",
      header: "작업",
      render: (row) => {
        const allowed = row.available_actions.includes("confirm_after_reconciliation") && row.confirmation_eligible && !mockMode;
        return (
          <button
            className="secondary-action"
            type="button"
            disabled={!allowed || confirm.isPending}
            onClick={() =>
              confirm.mutate({
                reconciliation_id: row.reconciliation_evidence?.reconciliation_id ?? latest?.reconciliation_id ?? null,
                account_id: row.account_id,
                as_of_date: row.reconciliation_evidence?.as_of_date ?? latest?.as_of_date ?? null,
                execution_ids: [row.manual_execution_id],
              })
            }
          >
            정산 증거로 확정
          </button>
        );
      },
    },
  ];

  return (
    <div className="page executions-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">PENDING MANUAL EXECUTIONS</p>
          <h1>실행 기록 정산 확인</h1>
          <p>이미 기록된 수동 실행이 실제 계좌 정산과 일치하는지 확인하는 단계입니다.</p>
        </div>
        <span className="read-only-tag">NO BROKER WRITE</span>
      </header>

      <section className="reconciliation-authority" aria-label="실행 확정 안전 경계">
        <article>
          <div>
            <strong>이 작업은 주문 실행이 아닙니다.</strong>
            <p>Portfolio OS는 브로커 주문을 보내지 않습니다.</p>
          </div>
        </article>
        <article>
          <div>
            <strong>passed reconciliation evidence 없이는 실행 기록을 확정할 수 없습니다.</strong>
            <p>정산 증거와 confirmed transaction만 확정 대상입니다.</p>
          </div>
        </article>
        <article>
          <div>
            <strong>정산은 최종 확인 경계입니다.</strong>
            <p>failed 또는 needs_review 정산은 실행 기록을 확정하지 않습니다.</p>
          </div>
        </article>
      </section>

      {mockMode ? <div className="inline-error" role="status">MOCK MODE에서는 실행 기록 확정을 만들 수 없습니다.</div> : null}
      {executions.error || reconciliation.error || confirm.error ? (
        <div className="inline-error" role="alert">{errorMessage(executions.error ?? reconciliation.error ?? confirm.error)}</div>
      ) : null}

      <div className="authority-grid authority-grid--recon">
        <article className="summary-card">
          <span>Pending Executions</span>
          <strong>{executions.data?.count ?? 0}</strong>
        </article>
        <article className="summary-card">
          <span>Latest Reconciliation</span>
          <strong>{latest ? latest.reconciliation_status : "none"}</strong>
        </article>
        <article className="summary-card">
          <span>As Of</span>
          <strong>{formatDate(latest?.as_of_date)}</strong>
        </article>
        <article className="summary-card">
          <span>Eligible</span>
          <strong>{executions.data?.executions.filter((row) => row.confirmation_eligible).length ?? 0}</strong>
        </article>
      </div>

      {confirm.data ? (
        <section className="panel">
          <div className="panel__header">
            <div>
              <p className="eyebrow">CONFIRMATION RESULT</p>
              <h2>확정 결과</h2>
            </div>
            <span className="mono">{confirm.data.confirmation_run_id}</span>
          </div>
          <div className="confirmation-result-grid">
            <article>
              <strong>Confirmed</strong>
              <p>{confirm.data.confirmed_execution_ids.join(", ") || "-"}</p>
            </article>
            <article>
              <strong>Still Pending</strong>
              <p>{confirm.data.still_pending_execution_ids.join(", ") || "-"}</p>
            </article>
            <article>
              <strong>Failed</strong>
              <p>{confirm.data.failed_execution_ids.join(", ") || "-"}</p>
            </article>
            <article>
              <strong>Skipped</strong>
              <p>{confirm.data.skipped_executions.map((item) => `${item.execution_id ?? "-"}:${item.reason}`).join(", ") || "-"}</p>
            </article>
          </div>
          <p className="panel__note">{confirm.data.explanation}</p>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel__header">
          <div>
            <p className="eyebrow">QUEUE</p>
            <h2>정산 대기 실행 기록</h2>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={executions.data?.executions ?? []}
          rowKey={(row) => row.manual_execution_id}
          emptyMessage="정산을 기다리는 수동 실행 기록이 없습니다."
          caption="정산 대기 수동 실행 기록"
        />
      </section>
    </div>
  );
}
