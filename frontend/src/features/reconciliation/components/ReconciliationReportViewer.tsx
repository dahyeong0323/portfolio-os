import { ScrollText } from "lucide-react";
import type { ReconciliationReportResponse } from "../../../api/types";
import { formatDateTime } from "../../../lib/format";

interface ReportViewerProps {
  report: ReconciliationReportResponse | undefined;
  pending: boolean;
  error: string | null;
  requested: boolean;
  available: boolean;
  onRequest: () => void;
}

export function ReconciliationReportViewer(props: ReportViewerProps) {
  return (
    <section className="panel reconciliation-workspace" aria-labelledby="report-viewer-title">
      <div className="panel__header"><div><p className="eyebrow">STEP 5 · REPORT</p><h2 id="report-viewer-title">정산 보고서</h2></div><span>PLAINTEXT MARKDOWN</span></div>
      {!props.requested && <div className="report-gate"><ScrollText aria-hidden="true" /><div><strong>생성된 Markdown 보고서를 조회합니다.</strong><p>보고서 HTML은 실행하지 않고 텍스트로만 표시합니다.</p></div><button className="secondary-action" type="button" onClick={props.onRequest} disabled={!props.available}>보고서 불러오기</button></div>}
      {props.pending && <div className="empty-state"><span>LOADING</span><p>보고서를 불러오는 중입니다.</p></div>}
      {props.error && <div className="inline-error" role="alert">{props.error}</div>}
      {props.report && <div className="report-content"><div><span>{props.report.format}</span><time>{formatDateTime(props.report.generated_at)}</time></div><pre>{props.report.content}</pre></div>}
    </section>
  );
}
