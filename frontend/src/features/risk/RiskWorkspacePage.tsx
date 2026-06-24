import { AlertTriangle, CheckCircle2, FileCheck2, ShieldCheck, Ticket, XCircle } from "lucide-react";
import { FormEvent, useMemo, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { useAccountsQuery } from "../../api/queries/accounts";
import { useInstrumentsQuery } from "../../api/queries/instruments";
import { useCreateIntent, useValidateIntent } from "../../api/queries/intents";
import { useCreateTicketFromValidation } from "../../api/queries/tickets";
import { apiRuntime } from "../../api/client";
import type { CreateIntentRequest, CreateIntentResponse, CreateTicketResponse, ValidateIntentResponse } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { errorMessage } from "../../lib/guards";
import { formatDate, formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { ledgerStatusMap, riskValidationStatusMap } from "../../lib/statusMap";

type FormState = {
  accountId: string;
  instrumentId: string;
  side: "buy" | "sell";
  amountMode: "quantity" | "notional";
  quantity: string;
  notional: string;
  limitPrice: string;
  currency: string;
  rationale: string;
  asOfDate: string;
};

const today = new Date().toISOString().slice(0, 10);

const initialForm: FormState = {
  accountId: "",
  instrumentId: "",
  side: "buy",
  amountMode: "notional",
  quantity: "",
  notional: "",
  limitPrice: "",
  currency: "USD",
  rationale: "",
  asOfDate: today,
};

function decimalOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function validationTone(status: string) {
  if (status === "passed") return "green";
  if (status === "adjusted") return "amber";
  return "red";
}

export function RiskWorkspacePage() {
  const accounts = useAccountsQuery();
  const instruments = useInstrumentsQuery();
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const createIntent = useCreateIntent();
  const validateIntent = useValidateIntent();
  const createTicket = useCreateTicketFromValidation();
  const [form, setForm] = useState<FormState>(initialForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [intentResult, setIntentResult] = useState<CreateIntentResponse | null>(null);
  const [validationResult, setValidationResult] = useState<ValidateIntentResponse | null>(null);
  const [ticketResult, setTicketResult] = useState<CreateTicketResponse | null>(null);

  const selectedAccount = accounts.data?.accounts.find((account) => String(account.account_id) === form.accountId);
  const selectedInstrument = instruments.data?.instruments.find((instrument) => String(instrument.instrument_id) === form.instrumentId);
  const mockMode = runtime.source === "mock";
  const canCreateTicket = validationResult?.validation.validation_status === "passed" || validationResult?.validation.validation_status === "adjusted";
  const activeStep = ticketResult ? 4 : validationResult ? 3 : intentResult ? 2 : 1;

  const checkColumns: DataColumn<ValidateIntentResponse["validation"]["checks"][number]>[] = [
    { key: "code", header: "체크", render: (row) => <span className="mono">{row.check_code}</span> },
    { key: "status", header: "상태", render: (row) => <StatusBadge label={row.status} tone={row.status === "failed" ? "red" : row.status === "adjusted" ? "amber" : row.status === "warning" ? "yellow" : "green"} /> },
    { key: "message", header: "설명", render: (row) => row.message },
    { key: "observed", header: "관측값", align: "right", render: (row) => formatDecimal(row.observed_value) },
    { key: "adjusted", header: "조정값", align: "right", render: (row) => formatDecimal(row.adjusted_value) },
  ];

  const intentPayload = useMemo<CreateIntentRequest | null>(() => {
    if (!form.accountId || !form.instrumentId) return null;
    const requestedQuantity = form.amountMode === "quantity" ? decimalOrNull(form.quantity) : null;
    const requestedNotional = form.amountMode === "notional" ? decimalOrNull(form.notional) : null;
    return {
      account_id: Number(form.accountId),
      instrument_id: Number(form.instrumentId),
      side: form.side,
      currency: form.currency.trim().toUpperCase(),
      requested_quantity: requestedQuantity,
      requested_notional: requestedNotional,
      limit_price: decimalOrNull(form.limitPrice),
      rationale: form.rationale.trim() || null,
    };
  }, [form]);

  async function handleCreateIntent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setValidationResult(null);
    setTicketResult(null);
    if (mockMode) {
      setFormError("Mock mode에서는 공식 의도를 생성할 수 없습니다.");
      return;
    }
    if (!intentPayload) {
      setFormError("계좌와 종목을 선택하세요.");
      return;
    }
    if (!intentPayload.requested_quantity && !intentPayload.requested_notional) {
      setFormError("수량 또는 금액 중 하나를 입력하세요.");
      return;
    }
    try {
      const result = await createIntent.mutateAsync(intentPayload);
      setIntentResult(result);
    } catch {
      // React Query stores the structured error for rendering below.
    }
  }

  async function handleValidate() {
    if (!intentResult) return;
    setFormError(null);
    try {
      const result = await validateIntent.mutateAsync({
        intentId: intentResult.intent.intent_id,
        payload: { as_of_date: form.asOfDate || null },
      });
      setValidationResult(result);
      setTicketResult(null);
    } catch {
      // React Query stores the structured error for rendering below.
    }
  }

  async function handleCreateTicket() {
    const currentValidation = validationResult;
    if (!currentValidation?.validation.risk_validation_id) return;
    setFormError(null);
    try {
      const result = await createTicket.mutateAsync({ risk_validation_id: currentValidation.validation.risk_validation_id });
      setTicketResult(result);
    } catch {
      // React Query stores the structured error for rendering below.
    }
  }

  return (
    <div className="page risk-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">RISK-GATED OPERATING LOOP</p>
          <h1>리스크 엔진</h1>
          <p>의도 생성, 공식 Risk Engine 검증, 수동 주문 티켓 생성을 한 화면에서 진행합니다.</p>
        </div>
        <span className="read-only-tag">NO EXECUTION</span>
      </header>

      <section className="reconciliation-authority" aria-label="Stage 4 권한 안내">
        <article><ShieldCheck aria-hidden="true" /><div><strong>Risk Engine만 권한 보유</strong><p>프런트엔드는 한도나 검증 결과를 계산하지 않습니다.</p></div></article>
        <article><Ticket aria-hidden="true" /><div><strong>이 티켓은 자동 주문이 아닙니다.</strong><p>실제 주문은 사용자가 증권사 화면에서 수동으로 실행해야 합니다.</p></div></article>
        <article><AlertTriangle aria-hidden="true" /><div><strong>Risk Engine 검증 없이는 공식 티켓을 생성할 수 없습니다.</strong><p>승인, 거절, 수정, 실행은 Stage 4 범위 밖입니다.</p></div></article>
      </section>

      <ol className="reconciliation-stepper" aria-label="운영 루프 진행 단계">
        {["의도 생성", "Risk 검증", "공식 티켓 생성", "티켓 검토"].map((label, index) => (
          <li key={label} className={activeStep === index + 1 ? "is-active" : activeStep > index + 1 ? "is-complete" : undefined}>
            <span className="reconciliation-stepper__marker">{activeStep > index + 1 ? <CheckCircle2 aria-hidden="true" /> : index + 1}</span>
            <span><small>STEP {index + 1}</small><strong>{label}</strong></span>
          </li>
        ))}
      </ol>

      <div className="risk-grid">
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">STEP 1</p><h2>의도 생성</h2></div></div>
          <form className="snapshot-import-form" onSubmit={handleCreateIntent}>
            <div className="form-grid">
              <label className="field-label">계좌
                <select value={form.accountId} onChange={(event) => setForm({ ...form, accountId: event.target.value })}>
                  <option value="">계좌 선택</option>
                  {accounts.data?.accounts.map((account) => <option key={account.account_id} value={account.account_id}>{account.account_name} · {account.institution_name}</option>)}
                </select>
              </label>
              <label className="field-label">종목
                <select value={form.instrumentId} onChange={(event) => {
                  const instrument = instruments.data?.instruments.find((item) => String(item.instrument_id) === event.target.value);
                  setForm({ ...form, instrumentId: event.target.value, currency: instrument?.currency ?? form.currency });
                }}>
                  <option value="">종목 선택</option>
                  {instruments.data?.instruments.map((instrument) => <option key={instrument.instrument_id} value={instrument.instrument_id}>{instrument.symbol} · {instrument.instrument_name}</option>)}
                </select>
              </label>
              <label className="field-label">방향
                <select value={form.side} onChange={(event) => setForm({ ...form, side: event.target.value as "buy" | "sell" })}>
                  <option value="buy">자산 편입 의도</option>
                  <option value="sell">자산 축소 의도</option>
                </select>
              </label>
              <label className="field-label">입력 방식
                <select value={form.amountMode} onChange={(event) => setForm({ ...form, amountMode: event.target.value as "quantity" | "notional" })}>
                  <option value="notional">금액 기준</option>
                  <option value="quantity">수량 기준</option>
                </select>
              </label>
              {form.amountMode === "quantity" ? <label className="field-label">요청 수량<input inputMode="decimal" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })} /></label> : <label className="field-label">요청 금액<input inputMode="decimal" value={form.notional} onChange={(event) => setForm({ ...form, notional: event.target.value })} /></label>}
              <label className="field-label">지정가<input inputMode="decimal" value={form.limitPrice} onChange={(event) => setForm({ ...form, limitPrice: event.target.value })} /></label>
              <label className="field-label">통화<input value={form.currency} onChange={(event) => setForm({ ...form, currency: event.target.value.toUpperCase() })} maxLength={3} /></label>
              <label className="field-label">검증 기준일<input type="date" value={form.asOfDate} onChange={(event) => setForm({ ...form, asOfDate: event.target.value })} /></label>
            </div>
            <label className="field-label">사유 / 메모<textarea value={form.rationale} onChange={(event) => setForm({ ...form, rationale: event.target.value })} rows={3} /></label>
            {(formError || createIntent.error || validateIntent.error || createTicket.error) && <div className="inline-error" role="alert">{formError ?? errorMessage(createIntent.error ?? validateIntent.error ?? createTicket.error)}</div>}
            <div className="wizard-actions">
              <button className="primary-action" disabled={mockMode || createIntent.isPending} type="submit"><FileCheck2 aria-hidden="true" />의도 생성</button>
              {mockMode && <span>Mock mode에서는 공식 Stage 2 mutation이 비활성화됩니다.</span>}
            </div>
          </form>
        </section>

        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">STEP 2</p><h2>Risk Engine 검증</h2></div></div>
          <div className="risk-stage">
            {intentResult ? (
              <>
                <dl className="detail-list">
                  <div><dt>의도 ID</dt><dd className="mono">#{intentResult.intent.intent_id}</dd></div>
                  <div><dt>계좌</dt><dd>{selectedAccount?.account_name ?? intentResult.intent.account_id}</dd></div>
                  <div><dt>종목</dt><dd>{selectedInstrument?.symbol ?? intentResult.intent.instrument_id}</dd></div>
                  <div><dt>요청 금액</dt><dd>{formatMoney(intentResult.intent.requested_notional, intentResult.intent.currency)}</dd></div>
                </dl>
                <button className="primary-action" disabled={mockMode || validateIntent.isPending} onClick={handleValidate} type="button"><ShieldCheck aria-hidden="true" />Risk 검증 실행</button>
              </>
            ) : <div className="empty-state"><span>WAITING</span><p>먼저 거래 의도를 생성하세요.</p></div>}
          </div>
        </section>
      </div>

      {validationResult && <section className={`reconciliation-result reconciliation-result--${validationResult.validation.validation_status === "passed" ? "passed" : validationResult.validation.validation_status === "adjusted" ? "needs_review" : "failed"}`}>
        {validationResult.validation.validation_status === "rejected" ? <XCircle aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
        <div><h2>{validationResult.explanation}</h2><p>기준일 {formatDate(validationResult.validation.ledger_snapshot_as_of)} · 생성 {formatDateTime(validationResult.validation.created_at)}</p></div>
        <StatusBadge label={riskValidationStatusMap[validationResult.validation.validation_status].label} tone={validationTone(validationResult.validation.validation_status)} />
      </section>}

      {validationResult && <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">RISK CHECKS</p><h2>검증 결과</h2></div><StatusBadge label={ledgerStatusMap[validationResult.validation.ledger_status_at_validation].label} tone={ledgerStatusMap[validationResult.validation.ledger_status_at_validation].tone} /></div>
        <DataTable columns={checkColumns} rows={validationResult.validation.checks} rowKey={(row) => row.check_code} emptyMessage="Risk check 결과가 없습니다." caption="Risk Engine 검증 결과" />
        {(validationResult.failed_checks.length > 0 || validationResult.warnings.length > 0) && <div className="risk-warning-list">
          {validationResult.failed_checks.map((check) => <p key={check.check_code}><strong>{check.check_code}</strong> {check.message}</p>)}
          {validationResult.warnings.map((warning) => <p key={warning}>{warning}</p>)}
        </div>}
      </section>}

      <div className="risk-grid">
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">STEP 3</p><h2>공식 주문 티켓 생성</h2></div></div>
          <div className="risk-stage">
            {validationResult ? (
              <>
                <dl className="detail-list">
                  <div><dt>승인 수량</dt><dd>{formatDecimal(validationResult.validation.approved_quantity)}</dd></div>
                  <div><dt>승인 금액</dt><dd>{formatMoney(validationResult.validation.approved_notional, validationResult.validation.currency)}</dd></div>
                  <div><dt>최대 허용 금액</dt><dd>{formatMoney(validationResult.validation.max_allowed_notional, validationResult.validation.currency)}</dd></div>
                </dl>
                <button className="primary-action" disabled={mockMode || !canCreateTicket || createTicket.isPending} onClick={handleCreateTicket} type="button"><Ticket aria-hidden="true" />공식 티켓 생성</button>
                {!canCreateTicket && <p className="panel__note">거절된 Risk 검증은 공식 티켓을 만들 수 없습니다.</p>}
              </>
            ) : <div className="empty-state"><span>LOCKED</span><p>Risk Engine 검증 이후에만 티켓 생성이 열립니다.</p><button className="primary-action" disabled type="button"><Ticket aria-hidden="true" />공식 티켓 생성</button></div>}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">STEP 4</p><h2>티켓 검토</h2></div></div>
          <div className="risk-stage">
            {ticketResult ? (
              <>
                <dl className="detail-list">
                  <div><dt>티켓 ID</dt><dd className="mono">#TKT-{ticketResult.ticket.order_ticket_id}</dd></div>
                  <div><dt>상태</dt><dd>{ticketResult.ticket.status}</dd></div>
                  <div><dt>차단 액션</dt><dd>{ticketResult.blocked_actions.join(", ")}</dd></div>
                </dl>
                <Link className="secondary-action" to={`/tickets/${ticketResult.ticket.order_ticket_id}`}>티켓 상세 보기</Link>
              </>
            ) : <div className="empty-state"><span>NO TICKET</span><p>공식 티켓이 생성되면 상세 검토 링크가 표시됩니다.</p></div>}
          </div>
        </section>
      </div>
    </div>
  );
}
