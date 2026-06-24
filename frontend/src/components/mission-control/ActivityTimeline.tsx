import { CheckCircle2, Clock3, FileCheck2, Workflow } from "lucide-react";
import type { DecisionJournalListResponse, LatestReconciliationResponse, OrderTicketListResponse, OverrideListResponse, PendingExecutionListResponse } from "../../api/types";
import { formatDateTime } from "../../lib/format";

interface Activity { id: string; at: string; label: string; type: string; icon: typeof Clock3 }

export function ActivityTimeline({
  reconciliation,
  tickets,
  executions,
  overrides,
  journal,
}: {
  reconciliation?: LatestReconciliationResponse;
  tickets?: OrderTicketListResponse;
  executions?: PendingExecutionListResponse;
  overrides?: OverrideListResponse;
  journal?: DecisionJournalListResponse;
}) {
  const activities: Activity[] = [];
  if (reconciliation?.reconciliation?.completed_at) {
    activities.push({ id: `r-${reconciliation.reconciliation.reconciliation_id}`, at: reconciliation.reconciliation.completed_at, label: `정산 ${reconciliation.reconciliation.reconciliation_status}`, type: "RECON", icon: CheckCircle2 });
  }
  tickets?.tickets.forEach((ticket) => {
    const at = ticket.updated_at ?? ticket.created_at;
    if (at) activities.push({ id: `t-${ticket.order_ticket_id}`, at, label: `티켓 #${ticket.order_ticket_id} · ${ticket.status}`, type: "TICKET", icon: FileCheck2 });
  });
  executions?.executions.forEach((execution) => {
    activities.push({ id: `e-${execution.manual_execution_id}`, at: execution.executed_at, label: `수동 실행 기록 #${execution.manual_execution_id} · 정산 대기`, type: "EXEC", icon: Clock3 });
  });
  overrides?.overrides.forEach((override) => {
    if (override.created_at) activities.push({ id: `o-${override.override_id}`, at: override.created_at, label: `오버라이드 #${override.override_id} · ${override.status}`, type: "OVERRIDE", icon: Workflow });
  });
  journal?.entries.forEach((entry) => {
    activities.push({ id: `j-${entry.decision_id}`, at: entry.created_at, label: `저널 #${entry.decision_id} · ${entry.decision_type}`, type: "JOURNAL", icon: FileCheck2 });
  });
  activities.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

  return (
    <section className="panel activity-timeline">
      <div className="panel__header"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>최근 활동 타임라인</h2></div></div>
      {activities.length === 0 ? <div className="empty-state"><span>NO EVENTS</span><p>표시할 최근 이벤트가 없습니다.</p></div> : (
        <ol>
          {activities.slice(0, 6).map((activity) => {
            const Icon = activity.icon;
            return <li key={activity.id}><Icon aria-hidden="true" /><time>{formatDateTime(activity.at)}</time><strong>{activity.label}</strong><span>{activity.type}</span></li>;
          })}
        </ol>
      )}
    </section>
  );
}
