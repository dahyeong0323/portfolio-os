import { useSyncExternalStore } from "react";
import { useParams } from "react-router-dom";
import { apiRuntime } from "../../api/client";
import { useCancelOverride, useConfirmOverride, useOverrideById } from "../../api/queries/overrides";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable } from "../../components/tables/DataTable";
import { formatDate, formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

export function OverrideDetailPage() {
  const params = useParams();
  const overrideId = Number(params.overrideId);
  const detail = useOverrideById(Number.isFinite(overrideId) ? overrideId : null);
  const confirm = useConfirmOverride();
  const cancel = useCancelOverride();
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const mockMode = runtime.source === "mock";
  const data = detail.data;
  const override = data?.override;
  const canConfirm = Boolean(override?.available_actions.includes("confirm_override")) && !mockMode;
  const canCancel = Boolean(override?.available_actions.includes("cancel_override")) && !mockMode;
  const target = override?.instrument_symbol ?? override?.instrument_name ?? (override?.instrument_id ? `#${override.instrument_id}` : "-");

  return (
    <div className="page overrides-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">OVERRIDE DETAIL</p>
          <h1>오버라이드 #{overrideId}</h1>
          <p>예외 선언의 사유, 경고, 복기 일정, 감사 관계를 확인합니다.</p>
        </div>
        <span className="read-only-tag">DECLARED EXCEPTION</span>
      </header>
      {(detail.error || confirm.error || cancel.error) ? <div className="inline-error" role="alert">{errorMessage(detail.error ?? confirm.error ?? cancel.error)}</div> : null}
      {mockMode ? <div className="inline-error" role="status">MOCK MODE에서는 확인/취소 mutation이 비활성화됩니다.</div> : null}
      {!override ? <div className="empty-state"><span>LOADING</span><p>오버라이드 상세를 불러오는 중입니다.</p></div> : (
        <>
          <section className="panel">
            <div className="panel__header"><div><p className="eyebrow">WARNING</p><h2>공식 Risk 검증 흐름이 아닙니다</h2></div><StatusBadge label={override.status} tone={override.status === "cancelled" ? "gray" : "amber"} /></div>
            <dl className="detail-list">
              <div><dt>위험 경고</dt><dd>{override.risk_warning}</dd></div>
              <div><dt>인간 사유</dt><dd>{override.human_reason}</dd></div>
              <div><dt>계좌</dt><dd>{override.account_name ?? `#${override.account_id}`}</dd></div>
              <div><dt>대상</dt><dd>{target}</dd></div>
              <div><dt>선언 시 레저</dt><dd>{override.ledger_status_at_declaration}</dd></div>
              <div><dt>요청</dt><dd>{override.side ?? "-"} · {override.requested_quantity ? formatDecimal(override.requested_quantity) : formatMoney(override.requested_notional, override.currency ?? "")}</dd></div>
              <div><dt>정산 기한</dt><dd>{formatDate(override.mandatory_reconciliation_deadline)}</dd></div>
              <div><dt>복기 예정</dt><dd>{formatDate(override.mandatory_postmortem_date)}</dd></div>
              <div><dt>생성</dt><dd>{formatDateTime(override.created_at)}</dd></div>
            </dl>
            <div className="ticket-action-grid">
              <button className="primary-action" disabled={!canConfirm || confirm.isPending} onClick={() => confirm.mutate({ overrideId: override.override_id, payload: {} })}>인간 확인 기록</button>
              <button className="secondary-action" disabled={!canCancel || cancel.isPending} onClick={() => cancel.mutate({ overrideId: override.override_id, payload: {} })}>오버라이드 취소</button>
            </div>
            <p className="panel__note">확인은 브로커 실행이 아닙니다. 이 화면은 예외 판단을 감사 기록으로 남길 뿐입니다.</p>
          </section>
          <section className="panel">
            <div className="panel__header"><div><p className="eyebrow">JOURNAL</p><h2>결정 저널</h2></div></div>
            <DataTable columns={[
              { key: "id", header: "ID", render: (row) => <span className="mono">#{row.decision_id}</span> },
              { key: "type", header: "유형", render: (row) => row.decision_type },
              { key: "decision", header: "결정", render: (row) => row.human_decision },
              { key: "reason", header: "사유", render: (row) => row.reason ?? "-" },
              { key: "created", header: "생성", render: (row) => formatDateTime(row.created_at) },
            ]} rows={data.linked_journal_entries} rowKey={(row) => row.decision_id} emptyMessage="결정 저널이 없습니다." caption="결정 저널" />
          </section>
          <section className="panel">
            <div className="panel__header"><div><p className="eyebrow">POSTMORTEM</p><h2>복기 태스크</h2></div></div>
            {data.postmortem_task ? <dl className="detail-list"><div><dt>상태</dt><dd>{data.postmortem_task.status}</dd></div><div><dt>기한</dt><dd>{formatDate(data.postmortem_task.due_date)}</dd></div><div><dt>질문</dt><dd>{data.postmortem_task.prompt_questions.join(" / ")}</dd></div></dl> : <div className="empty-state"><span>NO TASK</span><p>연결된 복기 태스크가 없습니다.</p></div>}
          </section>
        </>
      )}
    </div>
  );
}
