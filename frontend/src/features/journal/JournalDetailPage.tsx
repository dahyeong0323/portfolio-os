import { Link, useParams } from "react-router-dom";
import { useJournalEntryById } from "../../api/queries/journal";
import { formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function reportReferencesFromContext(context: Record<string, unknown>): string[] {
  const raw = [context.report_reference, context.report_references].flat();
  return raw.filter((item): item is string => (
    typeof item === "string" && (/^report_[A-Za-z0-9_-]+$/.test(item) || /^DEMO-REPORT-[A-Za-z0-9_-]+$/.test(item))
  ));
}

export function JournalDetailPage() {
  const params = useParams();
  const journalId = Number(params.journalId);
  const entry = useJournalEntryById(Number.isFinite(journalId) ? journalId : null);
  const reportReferences = entry.data ? reportReferencesFromContext(entry.data.context) : [];

  return (
    <div className="page journal-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">JOURNAL DETAIL</p>
          <h1>저널 #{journalId}</h1>
          <p>결정 기록 상세입니다. 이 기록은 주문 권한이나 Risk Engine 결과를 대체하지 않습니다.</p>
        </div>
        <span className="read-only-tag">READ ONLY</span>
      </header>
      {entry.error ? <div className="inline-error" role="alert">{errorMessage(entry.error)}</div> : null}
      {entry.data ? (
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">{entry.data.decision_type}</p><h2>{entry.data.human_decision}</h2></div></div>
          <dl className="detail-list">
            <div><dt>사유</dt><dd>{entry.data.reason ?? "-"}</dd></div>
            <div><dt>감정 상태</dt><dd>{entry.data.emotional_state ?? "-"}</dd></div>
            <div><dt>연결 override</dt><dd>{entry.data.override_ticket_id ?? "-"}</dd></div>
            <div><dt>연결 ticket</dt><dd>{entry.data.order_ticket_id ?? "-"}</dd></div>
            <div><dt>연결 execution</dt><dd>{entry.data.manual_execution_id ?? "-"}</dd></div>
            <div><dt>연결 risk</dt><dd>{entry.data.risk_validation_id ?? "-"}</dd></div>
            <div><dt>생성</dt><dd>{formatDateTime(entry.data.created_at)}</dd></div>
            {reportReferences.length > 0 ? (
              <div>
                <dt>Linked reports</dt>
                <dd>{reportReferences.map((reference) => <Link className="table-link mono linked-report-pill" key={reference} to={`/reports?reference=${encodeURIComponent(reference)}`}>{reference}</Link>)}</dd>
              </div>
            ) : null}
            <div><dt>Context</dt><dd><pre>{JSON.stringify(entry.data.context, null, 2)}</pre></dd></div>
          </dl>
        </section>
      ) : <div className="empty-state"><span>LOADING</span><p>저널을 불러오는 중입니다.</p></div>}
    </div>
  );
}
