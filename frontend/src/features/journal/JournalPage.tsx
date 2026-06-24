import { Link } from "react-router-dom";
import { useJournalEntries } from "../../api/queries/journal";
import type { DecisionJournalEntry } from "../../api/types";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function linkedTarget(row: DecisionJournalEntry) {
  if (row.override_ticket_id) return `OVR-${row.override_ticket_id}`;
  if (row.order_ticket_id) return `TKT-${row.order_ticket_id}`;
  if (row.manual_execution_id) return `EXEC-${row.manual_execution_id}`;
  if (row.risk_validation_id) return `RISK-${row.risk_validation_id}`;
  return "-";
}

export function JournalPage() {
  const journal = useJournalEntries();
  const columns: DataColumn<DecisionJournalEntry>[] = [
    { key: "id", header: "Journal", render: (row) => <Link className="table-link mono" to={`/journal/${row.decision_id}`}>#{row.decision_id}</Link> },
    { key: "type", header: "유형", render: (row) => row.decision_type },
    { key: "decision", header: "결정", render: (row) => row.human_decision },
    { key: "links", header: "연결", render: linkedTarget },
    { key: "reason", header: "사유", render: (row) => row.reason ?? "-" },
    { key: "emotion", header: "상태", render: (row) => row.emotional_state ?? "-" },
    { key: "created", header: "생성", render: (row) => formatDateTime(row.created_at) },
  ];
  return (
    <div className="page journal-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">DECISION MEMORY</p>
          <h1>저널 / 복기</h1>
          <p>결정의 이유와 감정 상태를 감사 기록으로 읽습니다. 추천이나 주문 권한이 아닙니다.</p>
        </div>
        <span className="read-only-tag">AUDIT MEMORY</span>
      </header>
      {journal.error ? <div className="inline-error" role="alert">{errorMessage(journal.error)}</div> : null}
      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">JOURNAL</p><h2>결정 저널 <span>{journal.data?.count ?? 0}</span></h2></div></div>
        <DataTable columns={columns} rows={journal.data?.entries ?? []} rowKey={(row) => row.decision_id} emptyMessage="결정 저널이 없습니다." caption="결정 저널" />
      </section>
    </div>
  );
}
