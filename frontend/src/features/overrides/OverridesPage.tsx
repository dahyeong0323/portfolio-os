import { useSyncExternalStore, useState } from "react";
import { Link } from "react-router-dom";
import { apiRuntime } from "../../api/client";
import { useAccountsQuery } from "../../api/queries/accounts";
import { useInstrumentsQuery } from "../../api/queries/instruments";
import { useDeclareOverride, useOverrides } from "../../api/queries/overrides";
import type { OverrideTicket } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { formatDate, formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function overrideTone(status: string) {
  if (status === "cancelled") return "gray" as const;
  if (status === "human_confirmed") return "amber" as const;
  return "red" as const;
}

function overrideAsset(row: OverrideTicket) {
  return row.instrument_symbol ?? row.instrument_name ?? (row.instrument_id ? `#${row.instrument_id}` : "-");
}

export function OverridesPage() {
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const mockMode = runtime.source === "mock";
  const overrides = useOverrides();
  const accounts = useAccountsQuery();
  const instruments = useInstrumentsQuery();
  const declareOverride = useDeclareOverride();
  const [form, setForm] = useState({
    override_type: "panic",
    account_id: "",
    instrument_id: "",
    side: "",
    requested_quantity: "",
    requested_notional: "",
    currency: "USD",
    human_reason: "",
    emotional_state: "",
  });
  const [reasonTouched, setReasonTouched] = useState(false);
  const reasonMissing = reasonTouched && form.human_reason.trim() === "";
  const accountRows = accounts.data?.accounts ?? [];
  const instrumentRows = instruments.data?.instruments ?? [];
  const selectedAccountId = form.account_id || (accountRows[0]?.account_id != null ? String(accountRows[0].account_id) : "");
  const canDeclare = !mockMode && selectedAccountId !== "" && form.human_reason.trim() !== "" && !declareOverride.isPending;

  const columns: DataColumn<OverrideTicket>[] = [
    { key: "id", header: "Override", render: (row) => <Link className="table-link mono" to={`/overrides/${row.override_id}`}>#OVR-{row.override_id}</Link> },
    { key: "status", header: "상태", render: (row) => <StatusBadge label={row.status} tone={overrideTone(row.status)} /> },
    { key: "type", header: "유형", render: (row) => row.override_type },
    { key: "asset", header: "대상", render: overrideAsset },
    { key: "amount", header: "수량 / 금액", render: (row) => row.requested_quantity ? formatDecimal(row.requested_quantity) : formatMoney(row.requested_notional, row.currency ?? "") },
    { key: "ledger", header: "선언 시 레저", render: (row) => row.ledger_status_at_declaration },
    { key: "postmortem", header: "복기 예정", render: (row) => formatDate(row.mandatory_postmortem_date) },
    { key: "created", header: "생성", render: (row) => formatDateTime(row.created_at) },
  ];

  return (
    <div className="page overrides-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">OVERRIDE CONTROL</p>
          <h1>오버라이드</h1>
          <p>공식 Risk Engine 검증 흐름이 아닌, 명시적 예외 선언과 감사 기록입니다.</p>
        </div>
        <span className="read-only-tag">NO BROKER WRITE</span>
      </header>

      <section className="reconciliation-authority" aria-label="오버라이드 안전 경계">
        <article><div><strong>Override는 공식 Risk Engine 검증 흐름이 아닙니다.</strong><p>공식 추천이나 자동 주문으로 해석하지 않습니다.</p></div></article>
        <article><div><strong>이 화면은 시스템 밖 행동을 남기기 위한 예외 선언입니다.</strong><p>명시적 인간 사유가 없으면 선언할 수 없습니다.</p></div></article>
        <article><div><strong>거래 실행은 사용자가 증권사 화면에서 직접 판단해야 합니다.</strong><p>Portfolio OS는 브로커 주문을 보내지 않습니다.</p></div></article>
      </section>

      {mockMode ? <div className="inline-error" role="status">MOCK MODE에서는 오버라이드 선언, 확인, 취소를 만들 수 없습니다.</div> : null}
      {(overrides.error || declareOverride.error) ? <div className="inline-error" role="alert">{errorMessage(overrides.error ?? declareOverride.error)}</div> : null}

      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">DECLARE</p><h2>예외 선언</h2></div></div>
        <form className="snapshot-import-form" onSubmit={(event) => {
          event.preventDefault();
          setReasonTouched(true);
          if (!canDeclare) return;
          declareOverride.mutate({
            override_type: form.override_type,
            account_id: Number(selectedAccountId),
            instrument_id: form.instrument_id ? Number(form.instrument_id) : null,
            side: form.side === "buy" || form.side === "sell" ? form.side : null,
            requested_quantity: form.requested_quantity || null,
            requested_notional: form.requested_notional || null,
            currency: form.currency || null,
            human_reason: form.human_reason,
            emotional_state: form.emotional_state || null,
          });
        }}>
          <div className="form-grid">
            <label className="field-label">유형<select value={form.override_type} onChange={(event) => setForm({ ...form, override_type: event.target.value })}><option value="panic">panic</option><option value="manual_correction">manual_correction</option><option value="thesis_conviction">thesis_conviction</option><option value="emergency_buy">emergency_buy</option><option value="other">other</option></select></label>
            <label className="field-label">계좌<select value={selectedAccountId} onChange={(event) => setForm({ ...form, account_id: event.target.value })}>{accountRows.map((account) => <option key={account.account_id} value={account.account_id}>{account.account_name}</option>)}</select></label>
            <label className="field-label">종목<select value={form.instrument_id} onChange={(event) => setForm({ ...form, instrument_id: event.target.value })}><option value="">선택 안 함</option>{instrumentRows.map((instrument) => <option key={instrument.instrument_id} value={instrument.instrument_id}>{instrument.symbol}</option>)}</select></label>
            <label className="field-label">방향<select value={form.side} onChange={(event) => setForm({ ...form, side: event.target.value })}><option value="">선택 안 함</option><option value="buy">buy</option><option value="sell">sell</option></select></label>
            <label className="field-label">수량<input value={form.requested_quantity} onChange={(event) => setForm({ ...form, requested_quantity: event.target.value })} placeholder="1.000000" /></label>
            <label className="field-label">금액<input value={form.requested_notional} onChange={(event) => setForm({ ...form, requested_notional: event.target.value })} placeholder="1000.00" /></label>
            <label className="field-label">통화<input value={form.currency} onChange={(event) => setForm({ ...form, currency: event.target.value.toUpperCase() })} maxLength={3} /></label>
            <label className="field-label">감정 상태<input value={form.emotional_state} onChange={(event) => setForm({ ...form, emotional_state: event.target.value })} placeholder="calm / stressed" /></label>
            <label className="field-label field-label--wide">인간 사유<textarea value={form.human_reason} onBlur={() => setReasonTouched(true)} onChange={(event) => setForm({ ...form, human_reason: event.target.value })} rows={3} /></label>
          </div>
          {reasonMissing ? <p className="failure-reason">오버라이드는 명시적 인간 사유가 필요합니다.</p> : null}
          <div className="wizard-actions"><button className="primary-action" disabled={!canDeclare}>오버라이드 선언</button><span>자동 주문, 브로커 연결, 공식 Risk 검증 우회가 아닙니다.</span></div>
        </form>
      </section>

      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">REGISTER</p><h2>오버라이드 목록 <span>{overrides.data?.open_count ?? 0} OPEN</span></h2></div></div>
        <DataTable columns={columns} rows={overrides.data?.overrides ?? []} rowKey={(row) => row.override_id} emptyMessage="등록된 오버라이드가 없습니다." caption="오버라이드 목록" />
      </section>
    </div>
  );
}
