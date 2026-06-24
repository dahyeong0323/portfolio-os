import type { HealthResponse, LedgerStatusResponse, LatestReconciliationResponse } from "../../api/types";
import { ledgerStatusMap, reconciliationStatusMap } from "../../lib/statusMap";
import { StatusBadge } from "../status/StatusBadge";

export function SystemStatusOverview({ health, ledger, reconciliation }: { health?: HealthResponse; ledger?: LedgerStatusResponse; reconciliation?: LatestReconciliationResponse }) {
  const ledgerDef = ledger ? ledgerStatusMap[ledger.ledger_status] : null;
  const reconciliationKey = reconciliation?.found && reconciliation.reconciliation ? reconciliation.reconciliation.reconciliation_status : "none";
  const reconDef = reconciliationStatusMap[reconciliationKey];
  const rows = [
    { label: "API / DB", badge: <StatusBadge label={health?.database_ready ? "정상" : "점검 필요"} tone={health?.database_ready ? "green" : "red"} /> },
    { label: "Migration", badge: <StatusBadge label={health?.migrations.ready ? `${health.migrations.applied_count}/${health.migrations.expected_count}` : "미완료"} tone={health?.migrations.ready ? "green" : "red"} /> },
    { label: "Ledger", badge: ledgerDef ? <StatusBadge label={ledgerDef.label} tone={ledgerDef.tone} /> : <StatusBadge label="확인 중" tone="gray" /> },
    { label: "Reconciliation", badge: <StatusBadge label={reconDef.label} tone={reconDef.tone} /> },
    { label: "Authority", badge: <StatusBadge label="READ ONLY" tone="cyan" /> },
  ];
  return <section className="panel system-overview"><div className="panel__header"><div><p className="eyebrow">SYSTEM STATUS</p><h2>시스템 상태 개요</h2></div></div><dl>{rows.map((row) => <div key={row.label}><dt>{row.label}</dt><dd>{row.badge}</dd></div>)}</dl></section>;
}
