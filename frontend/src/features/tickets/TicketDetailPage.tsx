import { FormEvent, useState, useSyncExternalStore } from "react";
import { Link, useParams } from "react-router-dom";
import { apiRuntime } from "../../api/client";
import { useLogManualExecution } from "../../api/queries/executions";
import { useApproveTicket, useRejectTicket, useTicketById } from "../../api/queries/tickets";
import type { OrderTicketEvent, RiskCheck } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { errorMessage } from "../../lib/guards";
import { riskValidationStatusMap, ticketStatusMap } from "../../lib/statusMap";

type DecisionMode = "approve" | "reject" | null;

const defaultExecutionForm = {
  filled_quantity: "",
  fill_price: "",
  fee: "0",
  tax: "0",
  executed_at: "",
  broker_reference: "",
  notes: "",
};

export function TicketDetailPage() {
  const params = useParams();
  const ticketId = params.ticketId ? Number(params.ticketId) : null;
  const detail = useTicketById(Number.isFinite(ticketId) ? ticketId : null);
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const mockMode = runtime.source === "mock";

  const approveTicket = useApproveTicket();
  const rejectTicket = useRejectTicket();
  const logExecution = useLogManualExecution();

  const [decisionMode, setDecisionMode] = useState<DecisionMode>(null);
  const [decisionNote, setDecisionNote] = useState("");
  const [emotionalState, setEmotionalState] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [executionForm, setExecutionForm] = useState(defaultExecutionForm);

  const eventColumns: DataColumn<OrderTicketEvent>[] = [
    { key: "event", header: "이벤트", render: (row) => row.event_type },
    { key: "from", header: "이전", render: (row) => row.from_status ?? "-" },
    { key: "to", header: "이후", render: (row) => row.to_status },
    { key: "time", header: "시각", render: (row) => formatDateTime(row.created_at) },
  ];
  const checkColumns: DataColumn<RiskCheck>[] = [
    { key: "code", header: "체크", render: (row) => <span className="mono">{row.check_code}</span> },
    { key: "status", header: "상태", render: (row) => <StatusBadge label={row.status} tone={row.status === "failed" ? "red" : row.status === "adjusted" ? "amber" : row.status === "warning" ? "yellow" : "green"} /> },
    { key: "message", header: "설명", render: (row) => row.message },
  ];

  if (detail.error) return <div className="page"><div className="inline-error" role="alert">{errorMessage(detail.error)}</div></div>;
  if (!detail.data) return <div className="page"><div className="empty-state empty-state--large"><span>LOADING</span><p>티켓 상세를 불러오는 중입니다.</p></div></div>;

  const { ticket, linked_intent: intent, linked_risk_validation: validation } = detail.data;
  const ticketDef = ticketStatusMap[ticket.status];
  const riskDef = riskValidationStatusMap[validation.validation_status];
  const canApprove = detail.data.available_actions.includes("approve_ticket") && !mockMode;
  const canReject = detail.data.available_actions.includes("reject_ticket") && !mockMode;
  const canLogExecution = detail.data.available_actions.includes("log_manual_execution") && !mockMode;
  const mutationError = approveTicket.error ?? rejectTicket.error ?? logExecution.error;

  const submitDecision = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (ticketId == null || decisionMode == null) return;
    setLocalError(null);
    try {
      if (decisionMode === "approve") {
        await approveTicket.mutateAsync({
          ticketId,
          payload: {
            approval_note: decisionNote || null,
            emotional_state: emotionalState || null,
          },
        });
      } else {
        if (!decisionNote.trim()) {
          setLocalError("거절 사유를 입력해야 합니다.");
          return;
        }
        await rejectTicket.mutateAsync({
          ticketId,
          payload: {
            rejection_reason: decisionNote,
            emotional_state: emotionalState || null,
          },
        });
      }
      setDecisionMode(null);
      setDecisionNote("");
      setEmotionalState("");
    } catch {
      // React Query exposes the structured error below.
    }
  };

  const submitManualExecution = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (ticketId == null) return;
    setLocalError(null);
    if (!executionForm.filled_quantity || !executionForm.fill_price || !executionForm.executed_at) {
      setLocalError("수량, 체결 가격, 실행 시각은 필수입니다.");
      return;
    }
    try {
      await logExecution.mutateAsync({
        ticket_id: ticketId,
        filled_quantity: executionForm.filled_quantity,
        fill_price: executionForm.fill_price,
        fee: executionForm.fee || "0",
        tax: executionForm.tax || "0",
        executed_at: executionForm.executed_at,
        broker_reference: executionForm.broker_reference || null,
        notes: executionForm.notes || null,
      });
      setExecutionForm(defaultExecutionForm);
    } catch {
      // React Query exposes the structured error below.
    }
  };

  return (
    <div className="page ticket-detail-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">ORDER TICKET DETAIL</p>
          <h1>티켓 검토 #{ticket.order_ticket_id}</h1>
          <p>공식 Risk Engine 검증을 통과한 수동 주문 티켓입니다. 이 화면은 승인과 기록만 담당합니다.</p>
        </div>
        <Link className="secondary-action" to="/tickets">목록으로</Link>
      </header>

      <section className="reconciliation-authority" aria-label="티켓 권한 안내">
        <article><div><strong>이 티켓은 자동 주문이 아닙니다.</strong><p>Portfolio OS는 브로커에 주문을 보내지 않습니다.</p></div></article>
        <article><div><strong>실제 주문은 사용자가 증권사 화면에서 수동으로 실행해야 합니다.</strong><p>이 화면은 사람이 이미 수행한 외부 행동을 기록합니다.</p></div></article>
        <article><div><strong>Risk Engine 검증 없이는 공식 티켓을 생성할 수 없습니다.</strong><p>승인도 실행이 아니며, 정산이 최종 확인 경계입니다.</p></div></article>
      </section>

      {(localError || mutationError) && <div className="inline-error" role="alert">{localError ?? errorMessage(mutationError)}</div>}
      {mockMode && <div className="inline-error" role="status">MOCK MODE에서는 승인, 거절, 수동 실행 기록을 만들 수 없습니다.</div>}

      <div className="authority-grid authority-grid--recon">
        <article className="summary-card"><span>티켓 상태</span><StatusBadge label={ticketDef.label} tone={ticketDef.tone} title={ticketDef.description} /></article>
        <article className="summary-card"><span>Risk 결과</span><StatusBadge label={riskDef.label} tone={riskDef.tone} title={riskDef.description} /></article>
        <article className="summary-card"><span>수량</span><strong>{formatDecimal(ticket.ticket_quantity)}</strong></article>
        <article className="summary-card"><span>금액</span><strong>{formatMoney(ticket.ticket_notional, ticket.currency)}</strong></article>
      </div>

      <div className="two-column">
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">TICKET</p><h2>주문 티켓 요약</h2></div></div>
          <dl className="detail-list">
            <div><dt>방향</dt><dd>{ticket.side === "buy" ? "자산 편입 의도" : "자산 축소 의도"}</dd></div>
            <div><dt>종목 ID</dt><dd>{ticket.instrument_id}</dd></div>
            <div><dt>지정가</dt><dd>{formatMoney(ticket.limit_price, ticket.currency)}</dd></div>
            <div><dt>만료</dt><dd>{formatDateTime(ticket.expires_at)}</dd></div>
            <div><dt>가능 액션</dt><dd>{detail.data.available_actions.join(", ") || "-"}</dd></div>
            <div><dt>차단 액션</dt><dd>{detail.data.blocked_actions.join(", ") || "-"}</dd></div>
          </dl>
        </section>
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">LINKED INTENT</p><h2>연결된 의도</h2></div></div>
          <dl className="detail-list">
            <div><dt>의도 ID</dt><dd className="mono">#{intent.intent_id}</dd></div>
            <div><dt>상태</dt><dd>{intent.status}</dd></div>
            <div><dt>요청 수량</dt><dd>{formatDecimal(intent.requested_quantity)}</dd></div>
            <div><dt>요청 금액</dt><dd>{formatMoney(intent.requested_notional, intent.currency)}</dd></div>
            <div><dt>생성</dt><dd>{formatDateTime(intent.created_at)}</dd></div>
          </dl>
        </section>
      </div>

      <section className="panel ticket-actions-panel">
        <div className="panel__header"><div><p className="eyebrow">HUMAN CONTROL</p><h2>사람 승인 및 기록</h2></div></div>
        <div className="ticket-action-grid">
          <button className="primary-action" type="button" disabled={!canApprove || approveTicket.isPending} onClick={() => { setDecisionMode("approve"); setDecisionNote(""); }}>
            티켓 승인
          </button>
          <button className="secondary-action" type="button" disabled={!canReject || rejectTicket.isPending} onClick={() => { setDecisionMode("reject"); setDecisionNote(""); }}>
            티켓 거절
          </button>
          <button className="secondary-action" type="button" disabled title="Stage 6에서 재검토">
            티켓 수정 Stage 6
          </button>
        </div>
        <p className="panel__note">승인은 주문 실행이 아닙니다. 승인 후에도 사용자가 증권사 화면에서 직접 수행한 체결 정보만 기록할 수 있습니다.</p>
      </section>

      {decisionMode && (
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">DECISION JOURNAL</p><h2>{decisionMode === "approve" ? "티켓 승인 기록" : "티켓 거절 기록"}</h2></div></div>
          <form className="snapshot-import-form" onSubmit={submitDecision}>
            <div className="form-grid">
              <label className="field-label">
                {decisionMode === "approve" ? "승인 메모" : "거절 사유"}
                <textarea value={decisionNote} onChange={(event) => setDecisionNote(event.target.value)} rows={4} required={decisionMode === "reject"} />
              </label>
              <label className="field-label">
                감정 상태 선택 입력
                <input value={emotionalState} onChange={(event) => setEmotionalState(event.target.value)} placeholder="예: 차분함, 보류 후 결정" />
              </label>
            </div>
            <div className="wizard-actions">
              <button className="primary-action" type="submit" disabled={mockMode || approveTicket.isPending || rejectTicket.isPending}>
                {decisionMode === "approve" ? "승인 기록 저장" : "거절 기록 저장"}
              </button>
              <button className="secondary-action" type="button" onClick={() => setDecisionMode(null)}>취소</button>
            </div>
          </form>
        </section>
      )}

      {ticket.status === "approved" && (
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">MANUAL EXECUTION LOG</p><h2>수동 실행 기록</h2></div></div>
          <form className="snapshot-import-form" onSubmit={submitManualExecution}>
            <div className="authority-notice">
              <div>
                <strong>이 버튼은 주문을 실행하지 않습니다.</strong>
                <p>증권사 화면에서 사용자가 직접 수행한 체결 정보를 Portfolio OS에 기록하는 단계입니다.</p>
              </div>
            </div>
            <div className="form-grid">
              <label className="field-label">체결 수량<input value={executionForm.filled_quantity} onChange={(event) => setExecutionForm({ ...executionForm, filled_quantity: event.target.value })} inputMode="decimal" /></label>
              <label className="field-label">체결 가격<input value={executionForm.fill_price} onChange={(event) => setExecutionForm({ ...executionForm, fill_price: event.target.value })} inputMode="decimal" /></label>
              <label className="field-label">수수료<input value={executionForm.fee} onChange={(event) => setExecutionForm({ ...executionForm, fee: event.target.value })} inputMode="decimal" /></label>
              <label className="field-label">세금<input value={executionForm.tax} onChange={(event) => setExecutionForm({ ...executionForm, tax: event.target.value })} inputMode="decimal" /></label>
              <label className="field-label">실행 시각<input type="datetime-local" value={executionForm.executed_at} onChange={(event) => setExecutionForm({ ...executionForm, executed_at: event.target.value })} /></label>
              <label className="field-label">브로커 참고번호<input value={executionForm.broker_reference} onChange={(event) => setExecutionForm({ ...executionForm, broker_reference: event.target.value })} placeholder="선택 입력" /></label>
              <label className="field-label field-label--wide">메모<textarea value={executionForm.notes} onChange={(event) => setExecutionForm({ ...executionForm, notes: event.target.value })} rows={3} /></label>
            </div>
            <div className="wizard-actions">
              <button className="primary-action" type="submit" disabled={!canLogExecution || logExecution.isPending}>수동 실행 기록 저장</button>
              <span>저장 후 상태는 정산 대기입니다.</span>
            </div>
          </form>
        </section>
      )}

      {logExecution.data && (
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">PENDING RECONCILIATION</p><h2>수동 실행 기록 완료</h2></div><StatusBadge label="정산 대기" tone="amber" /></div>
          <dl className="detail-list">
            <div><dt>실행 ID</dt><dd className="mono">#{logExecution.data.execution_id}</dd></div>
            <div><dt>생성된 provisional transaction</dt><dd className="mono">#{logExecution.data.created_transaction_id ?? "-"}</dd></div>
            <div><dt>상태</dt><dd>{logExecution.data.execution_status}</dd></div>
            <div><dt>설명</dt><dd>{logExecution.data.explanation}</dd></div>
          </dl>
        </section>
      )}

      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">RISK VALIDATION</p><h2>검증 체크</h2></div><span className="mono">#RV-{validation.risk_validation_id}</span></div>
        <DataTable columns={checkColumns} rows={validation.checks} rowKey={(row) => row.check_code} emptyMessage="검증 체크가 없습니다." caption="티켓 연결 Risk 검증 체크" />
      </section>

      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">TIMELINE</p><h2>티켓 이벤트</h2></div></div>
        <DataTable columns={eventColumns} rows={detail.data.ticket_events} rowKey={(row) => row.event_id} emptyMessage="티켓 이벤트가 없습니다." caption="티켓 이벤트 타임라인" />
      </section>
    </div>
  );
}
