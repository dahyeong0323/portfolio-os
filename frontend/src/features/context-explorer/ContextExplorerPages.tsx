import { BookOpenText, BrainCircuit, ClipboardList, FileText, Gauge, Layers3, Link2, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import {
  useGovernanceEvents,
  useGovernanceOverview,
  useMacroDetail,
  useMacroItems,
  useResearchDetail,
  useResearchItems,
  useSeniorMemoDetail,
  useSeniorMemos,
} from "../../api/queries/contextExplorer";
import type { MacroItem, ResearchItem, SeniorMemoItem } from "../../api/types";
import { formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function isSafeReportReference(value: string | null | undefined): value is string {
  return Boolean(value && (/^report_[A-Za-z0-9_-]+$/.test(value) || /^DEMO-REPORT-[A-Za-z0-9_-]+$/.test(value)));
}

function toDetailText(value: unknown): string {
  if (value == null) return "-";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function numericParam(value: string | undefined): string | null {
  return value && /^\d+$/.test(value) ? value : null;
}

function ReportLinks({ references }: { references: Array<string | null | undefined> }) {
  const safeReferences = references.filter(isSafeReportReference);
  if (safeReferences.length === 0) return <span className="muted">-</span>;
  return (
    <>
      {safeReferences.map((reference) => (
        <Link className="table-link linked-report-pill" key={reference} to={`/reports?reference=${encodeURIComponent(reference)}`}>
          <Link2 aria-hidden="true" /> {reference}
        </Link>
      ))}
    </>
  );
}

function ExplorerAuthority() {
  return (
    <section className="reconciliation-authority context-authority" aria-label="Context explorer authority boundaries">
      <article><ShieldCheck aria-hidden="true" /><div><strong>Context only</strong><p>Research, macro, senior memo, and governance records are evidence surfaces only.</p></div></article>
      <article><ClipboardList aria-hidden="true" /><div><strong>Risk path remains upstream</strong><p>Order creation and approval remain gated by the Stage 2 Risk Engine and ticket workflow.</p></div></article>
      <article><Layers3 aria-hidden="true" /><div><strong>Safe artifact links</strong><p>Report links use opaque references and route through the Reports Center.</p></div></article>
    </section>
  );
}

function DetailPre({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="context-detail-block">
      <h3>{title}</h3>
      <pre>{toDetailText(value)}</pre>
    </section>
  );
}

function EmptyDetail({ label }: { label: string }) {
  return <div className="empty-state empty-state--large"><FileText aria-hidden="true" /><span>SELECT ITEM</span><p>{label} 목록에서 항목을 선택하면 읽기 전용 상세 컨텍스트가 표시됩니다.</p></div>;
}

function ResearchTable({ items, selectedId }: { items: ResearchItem[]; selectedId: string | null }) {
  if (items.length === 0) return <div className="empty-state"><span>NO RESEARCH</span><p>표시할 Research context가 없습니다.</p></div>;
  return (
    <div className="data-table-wrap">
      <table className="data-table context-table">
        <caption className="sr-only">Research context list</caption>
        <thead><tr><th>title</th><th>instrument</th><th>thesis</th><th>anti</th><th>updated</th><th>report</th></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.research_id ?? item.title} className={selectedId === String(item.research_id) ? "is-selected" : undefined}>
              <td><Link className="table-link" to={`/research/${item.research_id}`}>{item.title}</Link><small>{item.subject}</small></td>
              <td>{item.instrument ?? "-"}</td>
              <td>{item.thesis ?? "-"}</td>
              <td><span className={`status-badge status-badge--${item.anti_thesis_present ? "amber" : "gray"}`}>{item.anti_thesis_present ? "PRESENT" : "NONE"}</span></td>
              <td className="mono">{formatDateTime(item.updated_at ?? item.created_at)}</td>
              <td><ReportLinks references={[item.linked_report_reference]} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ResearchDetailPanel({ researchId }: { researchId: string | null }) {
  const detail = useResearchDetail(researchId);
  if (!researchId) return <EmptyDetail label="Research" />;
  if (detail.isLoading) return <div className="empty-state empty-state--large"><span>LOADING</span><p>Research detail을 불러오는 중입니다.</p></div>;
  if (detail.error) return <div className="inline-error" role="alert">{errorMessage(detail.error)}</div>;
  if (!detail.data) return <EmptyDetail label="Research" />;
  return (
    <>
      <dl className="detail-list reports-metadata">
        <div><dt>Read-only</dt><dd>{detail.data.read_only_explanation}</dd></div>
        <div><dt>Reports</dt><dd><ReportLinks references={detail.data.linked_reports} /></dd></div>
        <div><dt>Blocked</dt><dd>{detail.data.blocked_actions.join(", ")}</dd></div>
      </dl>
      <DetailPre title="Metadata" value={detail.data.metadata} />
      <DetailPre title="Thesis" value={detail.data.thesis} />
      <DetailPre title="Anti-thesis" value={detail.data.anti_thesis} />
      <DetailPre title="Sources" value={detail.data.sources} />
      <DetailPre title="Evidence summary" value={detail.data.evidence_summary} />
    </>
  );
}

export function ResearchPage() {
  const params = useParams();
  const researchId = numericParam(params.researchId);
  const list = useResearchItems();
  return (
    <div className="page context-page">
      <header className="page-heading"><div><p className="eyebrow">RESEARCH EXPLORER</p><h1>Research Context</h1><p>투자 리서치 패킷과 근거를 읽기 전용으로 확인합니다.</p></div><span className="read-only-tag">READ ONLY</span></header>
      <ExplorerAuthority />
      {list.error ? <div className="inline-error" role="alert">{errorMessage(list.error)}</div> : null}
      <div className="context-layout">
        <section className="panel"><div className="panel__header"><div><p className="eyebrow">RESEARCH</p><h2>패킷 목록</h2></div><span>{list.isLoading ? "LOADING" : `${list.data?.count ?? 0} ITEMS`}</span></div><ResearchTable items={list.data?.items ?? []} selectedId={researchId} /></section>
        <section className="panel context-detail-panel"><div className="panel__header"><div><p className="eyebrow">DETAIL</p><h2>Research detail</h2></div><BookOpenText aria-hidden="true" /></div><ResearchDetailPanel researchId={researchId} /></section>
      </div>
    </div>
  );
}

function MacroTable({ items, selectedId }: { items: MacroItem[]; selectedId: string | null }) {
  if (items.length === 0) return <div className="empty-state"><span>NO MACRO</span><p>표시할 Macro context가 없습니다.</p></div>;
  return (
    <div className="data-table-wrap">
      <table className="data-table context-table">
        <caption className="sr-only">Macro context list</caption>
        <thead><tr><th>title</th><th>regime</th><th>scenario</th><th>tags</th><th>created</th><th>report</th></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.macro_id ?? item.title} className={selectedId === String(item.macro_id) ? "is-selected" : undefined}>
              <td><Link className="table-link" to={`/macro/${item.macro_id}`}>{item.title}</Link></td>
              <td>{item.regime ?? "-"}</td>
              <td>{item.scenario ?? "-"}</td>
              <td>{item.tags.map((tag) => <span className="status-badge status-badge--cyan context-tag" key={tag}>{tag}</span>)}</td>
              <td className="mono">{formatDateTime(item.created_at)}</td>
              <td><ReportLinks references={[item.linked_report_reference]} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MacroDetailPanel({ macroId }: { macroId: string | null }) {
  const detail = useMacroDetail(macroId);
  if (!macroId) return <EmptyDetail label="Macro" />;
  if (detail.isLoading) return <div className="empty-state empty-state--large"><span>LOADING</span><p>Macro detail을 불러오는 중입니다.</p></div>;
  if (detail.error) return <div className="inline-error" role="alert">{errorMessage(detail.error)}</div>;
  if (!detail.data) return <EmptyDetail label="Macro" />;
  return (
    <>
      <dl className="detail-list reports-metadata">
        <div><dt>Read-only</dt><dd>{detail.data.read_only_explanation}</dd></div>
        <div><dt>Reports</dt><dd><ReportLinks references={detail.data.linked_reports} /></dd></div>
        <div><dt>Blocked</dt><dd>{detail.data.blocked_actions.join(", ")}</dd></div>
      </dl>
      <DetailPre title="Metadata" value={detail.data.metadata} />
      <DetailPre title="Regime" value={detail.data.regime} />
      <DetailPre title="Scenario" value={detail.data.scenario} />
      <DetailPre title="Tags" value={detail.data.tags} />
    </>
  );
}

export function MacroPage() {
  const params = useParams();
  const macroId = numericParam(params.macroId);
  const list = useMacroItems();
  return (
    <div className="page context-page">
      <header className="page-heading"><div><p className="eyebrow">MACRO EXPLORER</p><h1>Macro Context</h1><p>거시 환경과 시나리오 태그를 주문 권한 없이 조회합니다.</p></div><span className="read-only-tag">READ ONLY</span></header>
      <ExplorerAuthority />
      {list.error ? <div className="inline-error" role="alert">{errorMessage(list.error)}</div> : null}
      <div className="context-layout">
        <section className="panel"><div className="panel__header"><div><p className="eyebrow">MACRO</p><h2>컨텍스트 목록</h2></div><span>{list.isLoading ? "LOADING" : `${list.data?.count ?? 0} ITEMS`}</span></div><MacroTable items={list.data?.items ?? []} selectedId={macroId} /></section>
        <section className="panel context-detail-panel"><div className="panel__header"><div><p className="eyebrow">DETAIL</p><h2>Macro detail</h2></div><Gauge aria-hidden="true" /></div><MacroDetailPanel macroId={macroId} /></section>
      </div>
    </div>
  );
}

function SeniorMemoTable({ memos, selectedId }: { memos: SeniorMemoItem[]; selectedId: string | null }) {
  if (memos.length === 0) return <div className="empty-state"><span>NO MEMOS</span><p>표시할 Senior Memo가 없습니다.</p></div>;
  return (
    <div className="data-table-wrap">
      <table className="data-table context-table">
        <caption className="sr-only">Senior memo list</caption>
        <thead><tr><th>title</th><th>ticket</th><th>risk</th><th>summary</th><th>created</th><th>report</th></tr></thead>
        <tbody>
          {memos.map((memo) => (
            <tr key={memo.memo_id ?? memo.title} className={selectedId === String(memo.memo_id) ? "is-selected" : undefined}>
              <td><Link className="table-link" to={`/senior-memos/${memo.memo_id}`}>{memo.title}</Link></td>
              <td>{memo.ticket_id ?? "-"}</td>
              <td>{memo.risk_validation_id ?? "-"}</td>
              <td>{memo.recommendation_summary ?? "-"}</td>
              <td className="mono">{formatDateTime(memo.created_at)}</td>
              <td><ReportLinks references={[memo.linked_report_reference]} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SeniorMemoDetailPanel({ memoId }: { memoId: string | null }) {
  const detail = useSeniorMemoDetail(memoId);
  if (!memoId) return <EmptyDetail label="Senior Memo" />;
  if (detail.isLoading) return <div className="empty-state empty-state--large"><span>LOADING</span><p>Senior Memo detail을 불러오는 중입니다.</p></div>;
  if (detail.error) return <div className="inline-error" role="alert">{errorMessage(detail.error)}</div>;
  if (!detail.data) return <EmptyDetail label="Senior Memo" />;
  return (
    <>
      <dl className="detail-list reports-metadata">
        <div><dt>Read-only</dt><dd>{detail.data.read_only_explanation}</dd></div>
        <div><dt>Reports</dt><dd><ReportLinks references={detail.data.linked_reports} /></dd></div>
        <div><dt>Blocked</dt><dd>{detail.data.blocked_actions.join(", ")}</dd></div>
      </dl>
      <DetailPre title="Metadata" value={detail.data.metadata} />
      <DetailPre title="Input bundle" value={detail.data.input_bundle} />
      <DetailPre title="Sections" value={detail.data.sections} />
      <DetailPre title="Decision candidates" value={detail.data.decision_candidates} />
      <DetailPre title="No-action alternatives" value={detail.data.no_action_alternatives} />
      <DetailPre title="Opposing arguments" value={detail.data.opposing_arguments} />
    </>
  );
}

export function SeniorMemosPage() {
  const params = useParams();
  const memoId = numericParam(params.memoId);
  const list = useSeniorMemos();
  return (
    <div className="page context-page">
      <header className="page-heading"><div><p className="eyebrow">SENIOR MEMO EXPLORER</p><h1>Senior Memos</h1><p>자문 메모를 주문 권한 없이 검토합니다.</p></div><span className="read-only-tag">READ ONLY</span></header>
      <ExplorerAuthority />
      {list.error ? <div className="inline-error" role="alert">{errorMessage(list.error)}</div> : null}
      <div className="context-layout">
        <section className="panel"><div className="panel__header"><div><p className="eyebrow">MEMOS</p><h2>메모 목록</h2></div><span>{list.isLoading ? "LOADING" : `${list.data?.count ?? 0} ITEMS`}</span></div><SeniorMemoTable memos={list.data?.memos ?? []} selectedId={memoId} /></section>
        <section className="panel context-detail-panel"><div className="panel__header"><div><p className="eyebrow">DETAIL</p><h2>Memo detail</h2></div><BrainCircuit aria-hidden="true" /></div><SeniorMemoDetailPanel memoId={memoId} /></section>
      </div>
    </div>
  );
}

export function GovernancePage() {
  const overview = useGovernanceOverview();
  const events = useGovernanceEvents();
  const data = overview.data;
  const warnings = data?.stale_context_warnings ?? [];
  const reportRefs = [
    ...(data?.governance_report_references ?? []),
    ...(data?.canary_report_references ?? []),
    ...(data?.health_report_references ?? []),
    ...(data?.context_report_references ?? []),
  ];
  return (
    <div className="page context-page">
      <header className="page-heading"><div><p className="eyebrow">GOVERNANCE EXPLORER</p><h1>Governance Context</h1><p>Context package, canary, health, and governance event state를 읽기 전용으로 확인합니다.</p></div><span className="read-only-tag">READ ONLY</span></header>
      <ExplorerAuthority />
      {[overview.error, events.error].filter(Boolean).length > 0 ? <div className="inline-error" role="alert">{errorMessage(overview.error ?? events.error)}</div> : null}
      <section className="authority-grid context-health-grid" aria-label="Governance context health">
        <article className="summary-card"><span>CONTEXT PACKAGE</span><strong>{data?.context_package_status ? "AVAILABLE" : "EMPTY"}</strong></article>
        <article className="summary-card"><span>CANARY</span><strong>{data?.canary ? "RECORDED" : "EMPTY"}</strong></article>
        <article className="summary-card"><span>HEALTH</span><strong>{data?.health ? "RECORDED" : "EMPTY"}</strong></article>
        <article className="summary-card"><span>WARNINGS</span><strong>{warnings.length}</strong></article>
      </section>
      <div className="context-layout">
        <section className="panel">
          <div className="panel__header"><div><p className="eyebrow">OVERVIEW</p><h2>Context health</h2></div><span>{overview.isLoading ? "LOADING" : "READ ONLY"}</span></div>
          <dl className="detail-list reports-metadata">
            <div><dt>Reports</dt><dd><ReportLinks references={reportRefs} /></dd></div>
            <div><dt>Blocked</dt><dd>{data?.blocked_actions.join(", ") ?? "create_order, approve, execute, broker_write"}</dd></div>
          </dl>
          {warnings.length === 0 ? <div className="empty-state"><span>NO WARNINGS</span><p>표시할 stale context warning이 없습니다.</p></div> : <div className="risk-warning-list">{warnings.map((warning) => <p key={warning}><strong>WARNING</strong> {warning}</p>)}</div>}
          <DetailPre title="Context package" value={data?.context_package_status} />
          <DetailPre title="Canary" value={data?.canary} />
          <DetailPre title="Health" value={data?.health} />
        </section>
        <section className="panel context-detail-panel">
          <div className="panel__header"><div><p className="eyebrow">EVENTS</p><h2>Governance events</h2></div><span>{events.isLoading ? "LOADING" : `${events.data?.count ?? 0} ITEMS`}</span></div>
          {(events.data?.events ?? []).length === 0 ? (
            <div className="empty-state empty-state--large"><span>NO EVENTS</span><p>표시할 governance event가 없습니다.</p></div>
          ) : (
            <div className="data-table-wrap">
              <table className="data-table context-table">
                <caption className="sr-only">Governance event list</caption>
                <thead><tr><th>event</th><th>scope</th><th>severity</th><th>related</th><th>created</th></tr></thead>
                <tbody>
                  {events.data!.events.map((event) => (
                    <tr key={event.event_id}>
                      <td>{event.event_type}<small>{event.event_summary}</small></td>
                      <td>{event.event_scope}</td>
                      <td><span className="status-badge status-badge--cyan">{event.severity}</span></td>
                      <td>{event.related_table && event.related_id ? `${event.related_table} #${event.related_id}` : "-"}</td>
                      <td className="mono">{formatDateTime(event.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
