import { AlertTriangle, CheckCircle2, Play } from "lucide-react";
import type { ExternalSnapshotImportResponse } from "../../../api/types";
import { formatDate, formatDateTime } from "../../../lib/format";

interface ArtifactSummaryProps {
  artifact: ExternalSnapshotImportResponse;
  pending: boolean;
  disabled: boolean;
  error: string | null;
  onRun: () => void;
  onReset: () => void;
}

export function ArtifactSummary({ artifact, pending, disabled, error, onRun, onReset }: ArtifactSummaryProps) {
  return (
    <section className="panel reconciliation-workspace" aria-labelledby="artifact-summary-title">
      <div className="panel__header">
        <div><p className="eyebrow">STEP 2 · NORMALIZED ARTIFACT</p><h2 id="artifact-summary-title">가져오기 결과 확인</h2></div>
        <span>{artifact.status === "imported" ? "IMPORTED" : "WARNINGS"}</span>
      </div>
      <div className="artifact-summary">
        <div className="artifact-meta">
          <CheckCircle2 aria-hidden="true" />
          <div><strong>{formatDate(artifact.as_of_date)} 스냅샷</strong><span>{artifact.source} · {formatDateTime(artifact.imported_at)}</span></div>
        </div>
        <dl className="count-grid">
          <div><dt>포지션</dt><dd>{artifact.counts.positions}</dd></div>
          <div><dt>현금</dt><dd>{artifact.counts.cash}</dd></div>
          <div><dt>부채</dt><dd>{artifact.counts.liabilities}</dd></div>
          <div><dt>세금 준비금</dt><dd>{artifact.counts.tax_reserves}</dd></div>
        </dl>
        {artifact.warnings.length > 0 && <div className="artifact-warnings" role="status"><AlertTriangle aria-hidden="true" /><div><strong>종목 매칭 확인 필요</strong>{artifact.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div></div>}
        {error && <div className="inline-error" role="alert">{error}</div>}
        <div className="wizard-actions">
          <button className="primary-action" type="button" onClick={onRun} disabled={disabled || pending}><Play aria-hidden="true" />{pending ? "정산 실행 중…" : "정산 실행"}</button>
          <button className="secondary-action" type="button" onClick={onReset} disabled={pending}>새 스냅샷 선택</button>
        </div>
      </div>
    </section>
  );
}
