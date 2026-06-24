import { AlertCircle, AlertTriangle, DatabaseZap, Info } from "lucide-react";
import type { HealthResponse, LedgerStatusResponse, LatestReconciliationResponse, OverrideListResponse, PendingExecutionListResponse, PostmortemTaskListResponse } from "../../api/types";

interface AlertItem { title: string; text: string; tone: "red" | "amber" | "cyan"; icon: typeof AlertTriangle }

interface AlertsPanelProps {
  health?: HealthResponse;
  ledger?: LedgerStatusResponse;
  reconciliation?: LatestReconciliationResponse;
  executions?: PendingExecutionListResponse;
  overrides?: OverrideListResponse;
  postmortems?: PostmortemTaskListResponse;
  isMock: boolean;
}

export function AlertsPanel({ health, ledger, reconciliation, executions, overrides, postmortems, isMock }: AlertsPanelProps) {
  const alerts: AlertItem[] = [];
  if (isMock) alerts.push({ title: "MOCK DATA ACTIVE", text: "실제 계좌 데이터가 아닌 샘플 응답입니다.", tone: "amber", icon: DatabaseZap });
  if (health && !health.database_ready) alerts.push({ title: "API DEGRADED", text: "데이터베이스 readiness를 확인하세요.", tone: "red", icon: AlertCircle });
  if (ledger?.ledger_status === "broken") alerts.push({ title: "LEDGER MISMATCH", text: "공식 흐름 전에 정산 차이를 확인해야 합니다.", tone: "red", icon: AlertTriangle });
  if (ledger?.ledger_status === "stale") alerts.push({ title: "RECONCILIATION STALE", text: "최근 정산의 허용 최신 범위를 벗어났습니다.", tone: "amber", icon: AlertTriangle });
  if (ledger?.ledger_status === "provisional") alerts.push({ title: "LEDGER PROVISIONAL", text: "미확정 입력 또는 수동 실행 기록이 정산을 기다립니다.", tone: "amber", icon: Info });
  if ((overrides?.open_count ?? 0) > 0) alerts.push({ title: "OPEN OVERRIDES", text: `${overrides?.open_count ?? 0}건의 선언된 예외가 감사 대기 중입니다.`, tone: "red", icon: AlertTriangle });
  if ((postmortems?.count ?? 0) > 0) alerts.push({ title: "POSTMORTEM DUE", text: `${postmortems?.count ?? 0}건의 복기 태스크가 예정되어 있습니다.`, tone: "amber", icon: Info });

  const reconStatus = reconciliation?.reconciliation?.reconciliation_status;
  if (reconStatus === "failed" || reconStatus === "needs_review") {
    alerts.push({ title: "RECONCILIATION REVIEW", text: reconciliation?.reconciliation?.failure_reason ?? "최신 정산 결과를 검토하세요.", tone: reconStatus === "failed" ? "red" : "amber", icon: AlertCircle });
  }
  if ((executions?.count ?? 0) > 0) alerts.push({ title: "PENDING RECONCILIATION", text: `${executions?.count ?? 0}건의 수동 실행 기록이 다음 정산 확인을 기다립니다.`, tone: "cyan", icon: Info });
  if (alerts.length === 0) alerts.push({ title: "NO ACTIVE ALERTS", text: "현재 API 응답에서 발생한 경고가 없습니다.", tone: "cyan", icon: Info });

  return (
    <section className="panel alerts-panel">
      <div className="panel__header"><div><p className="eyebrow">ALERTS & WARNINGS</p><h2>알림 및 경고</h2></div></div>
      <div className="alert-list">
        {alerts.slice(0, 5).map((alert) => {
          const Icon = alert.icon;
          return <article className={`alert-item alert-item--${alert.tone}`} key={alert.title}><Icon aria-hidden="true" /><div><strong>{alert.title}</strong><p>{alert.text}</p></div></article>;
        })}
      </div>
    </section>
  );
}
