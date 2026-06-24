import { AlertOctagon, CheckCircle2, DatabaseZap, ShieldAlert } from "lucide-react";
import { useEffect, useMemo, useState, useSyncExternalStore, type FormEvent } from "react";
import { apiRuntime } from "../../api/client";
import { useAccountsQuery } from "../../api/queries/accounts";
import {
  useImportExternalSnapshot,
  useReconciliationById,
  useReconciliationQuery,
  useReconciliationReport,
  useRunReconciliation,
} from "../../api/queries/reconciliation";
import type { ExternalSnapshotImportResponse, RunReconciliationResponse } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { formatDate, formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";
import { ledgerStatusMap, reconciliationStatusMap } from "../../lib/statusMap";
import { ArtifactSummary } from "./components/ArtifactSummary";
import { ReconciliationDiffViewer } from "./components/ReconciliationDiffViewer";
import { ReconciliationReportViewer } from "./components/ReconciliationReportViewer";
import { ReconciliationStepper } from "./components/ReconciliationStepper";
import { SnapshotImportStep, type SnapshotFileKind, type SnapshotFiles } from "./components/SnapshotImportStep";

function todayText(): string {
  const today = new Date();
  const local = new Date(today.getTime() - today.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

export function ReconciliationPage() {
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const accounts = useAccountsQuery();
  const latest = useReconciliationQuery();
  const importMutation = useImportExternalSnapshot();
  const runMutation = useRunReconciliation();

  const [accountId, setAccountId] = useState("");
  const [asOfDate, setAsOfDate] = useState(todayText);
  const [files, setFiles] = useState<SnapshotFiles>({});
  const [artifact, setArtifact] = useState<ExternalSnapshotImportResponse | null>(null);
  const [runResult, setRunResult] = useState<RunReconciliationResponse | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [reportRequested, setReportRequested] = useState(false);

  useEffect(() => {
    if (!accountId) {
      const firstActive = accounts.data?.accounts.find((account) => account.is_active);
      if (firstActive) setAccountId(String(firstActive.account_id));
    }
  }, [accountId, accounts.data]);

  const detail = useReconciliationById(runResult?.reconciliation_id ?? null);
  const report = useReconciliationReport(runResult?.reconciliation_id ?? null, reportRequested);
  const latestResult = latest.data?.reconciliation ?? null;
  const displayResult = detail.data ?? null;
  const mockMode = runtime.source === "mock";
  const activeStep = reportRequested ? 5 : runResult ? 4 : runMutation.isPending ? 3 : artifact ? 2 : 1;
  const currentStatus = displayResult?.reconciliation_status ?? latestResult?.reconciliation_status ?? "none";
  const statusDefinition = reconciliationStatusMap[currentStatus];

  const selectedFiles = useMemo(() => Object.values(files).filter(Boolean), [files]);
  const mutationError = localError
    ?? (importMutation.error ? errorMessage(importMutation.error) : null)
    ?? (runMutation.error ? errorMessage(runMutation.error) : null);

  const handleImport = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    if (!accountId) { setLocalError("정산할 활성 계좌를 선택하세요."); return; }
    if (!asOfDate) { setLocalError("스냅샷 기준일을 선택하세요."); return; }
    if (selectedFiles.length === 0) { setLocalError("최소 한 개의 CSV 파일을 선택하세요."); return; }

    const formData = new FormData();
    formData.append("account_id", accountId);
    formData.append("as_of_date", asOfDate);
    if (files.positions) formData.append("positions_file", files.positions);
    if (files.cash) formData.append("cash_file", files.cash);
    if (files.liabilities) formData.append("liabilities_file", files.liabilities);
    if (files.taxReserves) formData.append("tax_reserves_file", files.taxReserves);

    try {
      const imported = await importMutation.mutateAsync(formData);
      setArtifact(imported);
      setRunResult(null);
      setReportRequested(false);
    } catch { /* mutation state renders the structured error */ }
  };

  const handleRun = async () => {
    if (!artifact) return;
    setLocalError(null);
    try {
      const result = await runMutation.mutateAsync({
        artifact_id: artifact.artifact_id,
        account_id: artifact.account_id,
        as_of_date: artifact.as_of_date,
      });
      setRunResult(result);
      setReportRequested(false);
    } catch { /* mutation state renders the structured error */ }
  };

  const resetWizard = () => {
    importMutation.reset();
    runMutation.reset();
    setArtifact(null);
    setRunResult(null);
    setFiles({});
    setLocalError(null);
    setReportRequested(false);
  };

  return (
    <div className="page reconciliation-page">
      <header className="page-heading">
        <div><p className="eyebrow">RECONCILIATION CONTROL</p><h1>정산</h1><p>외부 account snapshot을 내부 레저 진실과 비교하고 공식 ledger status를 갱신합니다.</p></div>
        <StatusBadge label={statusDefinition.label} tone={statusDefinition.tone} />
      </header>

      <section className="reconciliation-authority" aria-label="정산 권한 안내">
        <article><DatabaseZap aria-hidden="true" /><div><strong>레저 진실 유지</strong><p>외부 값은 expected를 대체하지 않습니다.</p></div></article>
        <article><ShieldAlert aria-hidden="true" /><div><strong>거래 승인 아님</strong><p>정산은 주문이나 실행 권한을 만들지 않습니다.</p></div></article>
        <article><AlertOctagon aria-hidden="true" /><div><strong>Broken은 숨기지 않음</strong><p>불일치와 needs_review 결과를 그대로 표시합니다.</p></div></article>
      </section>

      <section className="authority-grid authority-grid--recon">
        <article className="summary-card"><span>최근 정산</span><StatusBadge label={statusDefinition.label} tone={statusDefinition.tone} /></article>
        <article className="summary-card"><span>기준일</span><strong>{formatDate(displayResult?.as_of_date ?? latestResult?.as_of_date)}</strong></article>
        <article className="summary-card"><span>완료 시간</span><strong>{formatDateTime(displayResult?.completed_at ?? latestResult?.completed_at)}</strong></article>
        <article className="summary-card"><span>Ledger Status</span>{(displayResult ?? latestResult) ? <StatusBadge label={ledgerStatusMap[(displayResult ?? latestResult)!.ledger_status_after].label} tone={ledgerStatusMap[(displayResult ?? latestResult)!.ledger_status_after].tone} /> : <strong>-</strong>}</article>
      </section>

      {(latest.error || accounts.error) && <div className="inline-error" role="alert">{errorMessage(latest.error ?? accounts.error)}</div>}
      <ReconciliationStepper activeStep={activeStep} />

      <SnapshotImportStep
        accounts={accounts.data?.accounts ?? []}
        accountId={accountId}
        asOfDate={asOfDate}
        files={files}
        disabled={mockMode || accounts.isLoading}
        pending={importMutation.isPending}
        error={!artifact ? mutationError : null}
        onAccountChange={setAccountId}
        onDateChange={setAsOfDate}
        onFileChange={(kind: SnapshotFileKind, file) => setFiles((current) => ({ ...current, [kind]: file }))}
        onSubmit={handleImport}
      />

      {artifact && <ArtifactSummary artifact={artifact} pending={runMutation.isPending} disabled={mockMode} error={mutationError} onRun={handleRun} onReset={resetWizard} />}

      {runResult && <section className={`reconciliation-result reconciliation-result--${runResult.reconciliation_status}`} role="status" aria-live="polite">
        {runResult.reconciliation_status === "passed" ? <CheckCircle2 aria-hidden="true" /> : <AlertOctagon aria-hidden="true" />}<div><p className="eyebrow">STEP 3 · RECONCILIATION RESULT</p><h2>{reconciliationStatusMap[runResult.reconciliation_status].label}</h2><p>{runResult.explanation}</p></div><StatusBadge label={ledgerStatusMap[runResult.ledger_status].label} tone={ledgerStatusMap[runResult.ledger_status].tone} />
      </section>}

      {detail.isLoading && <div className="panel empty-state"><span>LOADING</span><p>정산 차이를 불러오는 중입니다.</p></div>}
      {detail.error && <div className="inline-error" role="alert">{errorMessage(detail.error)}</div>}
      {displayResult && <ReconciliationDiffViewer reconciliation={displayResult} />}
      {runResult && <ReconciliationReportViewer report={report.data} pending={report.isLoading} error={report.error ? errorMessage(report.error) : null} requested={reportRequested} available={runResult.report_available} onRequest={() => setReportRequested(true)} />}

      {mockMode && latestResult && !artifact && <section className="panel mock-reconciliation-preview"><div className="panel__header"><div><p className="eyebrow">SAMPLE ONLY</p><h2>비공식 샘플 정산 미리보기</h2></div><span>MOCK DATA</span></div><p>아래 샘플은 UI 확인용이며 공식 정산으로 저장되거나 ledger status를 변경하지 않습니다.</p><ReconciliationDiffViewer reconciliation={latestResult} /></section>}
    </div>
  );
}
