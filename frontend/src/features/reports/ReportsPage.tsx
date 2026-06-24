import { Clipboard, Download, FileText, Layers3, Link2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useReportByReference, useReportCategories, useReportDownload, useReports } from "../../api/queries/reports";
import type { ReportListItem } from "../../api/types";
import { formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function isSafeReportReference(value: string | null): value is string {
  return Boolean(value && (/^report_[A-Za-z0-9_-]+$/.test(value) || /^DEMO-REPORT-[A-Za-z0-9_-]+$/.test(value)));
}

function categoryStatus(count: number): string {
  return count > 0 ? `${count} REPORTS` : "EMPTY";
}

function linkedObject(report: ReportListItem): string {
  if (!report.linked_object_type || !report.linked_object_id) return "-";
  return `${report.linked_object_type} #${report.linked_object_id}`;
}

export function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialReference = searchParams.get("reference");
  const [category, setCategory] = useState<string | null>(null);
  const [selectedReference, setSelectedReference] = useState<string | null>(() => isSafeReportReference(initialReference) ? initialReference : null);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);

  const categories = useReportCategories();
  const reports = useReports({ category, limit: 100 });
  const selected = useReportByReference(selectedReference);
  const download = useReportDownload(selected.data?.available_actions.includes("download") ? selected.data.report_reference : null);

  useEffect(() => {
    if (selectedReference || !reports.data?.reports.length) return;
    const firstSafe = reports.data.reports.find((report) => isSafeReportReference(report.report_reference));
    if (firstSafe) setSelectedReference(firstSafe.report_reference);
  }, [reports.data?.reports, selectedReference]);

  useEffect(() => {
    if (!selectedReference || !reports.data?.reports.length) return;
    const stillVisible = reports.data.reports.some((report) => report.report_reference === selectedReference);
    const firstSafe = reports.data.reports.find((report) => isSafeReportReference(report.report_reference));
    if (!stillVisible && !searchParams.get("reference")) setSelectedReference(firstSafe?.report_reference ?? null);
  }, [reports.data?.reports, searchParams, selectedReference]);

  const visibleCategories = categories.data?.categories ?? [];
  const selectedReport = selected.data;
  const tableReports = reports.data?.reports ?? [];
  const errors = [categories.error, reports.error, selected.error].filter(Boolean);
  const selectedCategoryLabel = category ? visibleCategories.find((item) => item.category_id === category)?.label ?? category : "ALL";

  function chooseReport(reference: string) {
    if (!isSafeReportReference(reference)) return;
    setSelectedReference(reference);
    setCopyStatus(null);
    setSearchParams({ reference });
  }

  async function copyReport() {
    if (!selectedReport?.content) return;
    await navigator.clipboard?.writeText(selectedReport.content);
    setCopyStatus("COPIED");
  }

  return (
    <div className="page reports-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">REPORTS CENTER</p>
          <h1>리포트 센터</h1>
          <p>감사 자료와 생성된 보고서를 안전하게 조회합니다.</p>
        </div>
        <span className="read-only-tag">READ ONLY</span>
      </header>

      <section className="reconciliation-authority reports-authority" aria-label="Reports Center authority boundaries">
        <article><ShieldCheck aria-hidden="true" /><div><strong>이 리포트는 감사/검토 자료이며 주문 권한이 아닙니다.</strong><p>Risk Engine과 티켓 흐름을 대체하지 않습니다.</p></div></article>
        <article><Layers3 aria-hidden="true" /><div><strong>이 화면에서는 거래, 승인, 실행을 수행할 수 없습니다.</strong><p>보고서 조회, 복사, 로컬 다운로드만 제공합니다.</p></div></article>
        <article><FileText aria-hidden="true" /><div><strong>보고서 내용은 읽기 전용으로 표시됩니다.</strong><p>HTML은 실행하지 않고 텍스트로만 렌더링합니다.</p></div></article>
      </section>

      {errors.length > 0 ? <div className="inline-error" role="alert">{errorMessage(errors[0])}</div> : null}

      <div className="reports-layout">
        <aside className="panel reports-category-panel" aria-label="Report categories">
          <div className="panel__header"><div><p className="eyebrow">CATEGORY</p><h2>분류</h2></div><span>{selectedCategoryLabel}</span></div>
          <button type="button" className={!category ? "report-category is-active" : "report-category"} onClick={() => { setCategory(null); setSelectedReference(null); setSearchParams({}); }}>
            <span>전체</span><strong>{reports.data?.count ?? 0}</strong>
          </button>
          {visibleCategories.map((item) => (
            <button type="button" key={item.category_id} className={category === item.category_id ? "report-category is-active" : "report-category"} onClick={() => { setCategory(item.category_id); setSelectedReference(null); setSearchParams({}); }}>
              <span>{item.label}</span>
              <small>{categoryStatus(item.report_count)}</small>
            </button>
          ))}
        </aside>

        <section className="panel reports-list-panel" aria-labelledby="reports-list-title">
          <div className="panel__header"><div><p className="eyebrow">CATALOG</p><h2 id="reports-list-title">보고서 목록</h2></div><span>{reports.isLoading ? "LOADING" : `${reports.data?.count ?? 0} ITEMS`}</span></div>
          {tableReports.length === 0 ? (
            <div className="empty-state"><span>NO REPORTS</span><p>이 분류에는 표시할 보고서가 없습니다.</p></div>
          ) : (
            <div className="data-table-wrap">
              <table className="data-table reports-table">
                <caption className="sr-only">Reports Center list</caption>
                <thead><tr><th>title</th><th>category</th><th>format</th><th>generated</th><th>linked object</th><th>status</th></tr></thead>
                <tbody>
                  {tableReports.map((report) => (
                    <tr key={report.report_reference} className={selectedReference === report.report_reference ? "is-selected" : undefined}>
                      <td><button type="button" className="table-link report-row-button" onClick={() => chooseReport(report.report_reference)}>{report.title}</button>{report.safe_summary ? <small>{report.safe_summary}</small> : null}</td>
                      <td>{report.category}</td>
                      <td><span className="status-badge status-badge--cyan">{report.format}</span></td>
                      <td className="mono">{formatDateTime(report.generated_at)}</td>
                      <td>{linkedObject(report)}</td>
                      <td><span className="status-badge status-badge--green">READ ONLY</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel reports-viewer-panel" aria-labelledby="report-viewer-title">
          <div className="panel__header">
            <div><p className="eyebrow">VIEWER</p><h2 id="report-viewer-title">{selectedReport?.title ?? "보고서 뷰어"}</h2></div>
            <span>{selectedReport?.format ?? "PLAINTEXT"}</span>
          </div>
          {!selectedReference ? (
            <div className="empty-state empty-state--large"><FileText aria-hidden="true" /><span>SELECT REPORT</span><p>목록에서 보고서를 선택하면 내용과 메타데이터가 여기에 표시됩니다.</p></div>
          ) : selected.isLoading ? (
            <div className="empty-state empty-state--large"><span>LOADING</span><p>보고서를 불러오는 중입니다.</p></div>
          ) : selectedReport ? (
            <>
              <dl className="detail-list reports-metadata">
                <div><dt>Reference</dt><dd className="mono">{selectedReport.report_reference}</dd></div>
                <div><dt>Generated</dt><dd>{formatDateTime(selectedReport.generated_at)}</dd></div>
                <div><dt>Linked object</dt><dd>{selectedReport.linked_object_type && selectedReport.linked_object_id ? `${selectedReport.linked_object_type} #${selectedReport.linked_object_id}` : "-"}</dd></div>
                <div><dt>Blocked actions</dt><dd>{selectedReport.blocked_actions.join(", ")}</dd></div>
              </dl>
              <div className="report-viewer-actions">
                <button className="secondary-action" type="button" onClick={copyReport}><Clipboard aria-hidden="true" />{copyStatus ?? "COPY"}</button>
                {download.href ? <a className="secondary-action" href={download.href}><Download aria-hidden="true" />DOWNLOAD</a> : null}
              </div>
              <div className="report-content report-center-content">
                <div><span>{selectedReport.format}</span><time>{formatDateTime(selectedReport.generated_at)}</time></div>
                <pre>{selectedReport.content}</pre>
              </div>
            </>
          ) : (
            <div className="empty-state empty-state--large"><span>NOT FOUND</span><p>선택한 보고서를 표시할 수 없습니다.</p></div>
          )}
        </section>
      </div>

      <section className="panel read-only-notice">
        <strong><Link2 aria-hidden="true" /> Reports Center boundary</strong>
        <p>이 화면은 기존 Markdown/JSON 산출물 조회 전용입니다. 주문 생성, 승인, 실행, 정산 확정, 브로커 쓰기 기능을 추가하지 않습니다.</p>
      </section>
    </div>
  );
}
