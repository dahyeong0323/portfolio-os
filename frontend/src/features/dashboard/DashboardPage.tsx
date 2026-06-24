import { Activity, BookOpenText, BrainCircuit, ClipboardList, Database, FileText, Gauge, Hourglass, ShieldCheck, Workflow } from "lucide-react";
import { useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { apiRuntime } from "../../api/client";
import { useAccountsQuery } from "../../api/queries/accounts";
import { useGovernanceOverview, useMacroItems, useResearchItems, useSeniorMemos } from "../../api/queries/contextExplorer";
import { useExecutionsQuery } from "../../api/queries/executions";
import { useHealthQuery } from "../../api/queries/health";
import { useInstrumentsQuery } from "../../api/queries/instruments";
import { useLedgerSnapshotQuery, useLedgerStatusQuery } from "../../api/queries/ledger";
import { useOverrides } from "../../api/queries/overrides";
import { usePostmortemTasks } from "../../api/queries/postmortems";
import { useReconciliationQuery } from "../../api/queries/reconciliation";
import { useReports } from "../../api/queries/reports";
import { useTicketsQuery } from "../../api/queries/tickets";
import { ActivityTimeline } from "../../components/mission-control/ActivityTimeline";
import { AlertsPanel } from "../../components/mission-control/AlertsPanel";
import { OpenTicketsPanel } from "../../components/mission-control/OpenTicketsPanel";
import { PendingActionsPanel } from "../../components/mission-control/PendingActionsPanel";
import { PortfolioThesisMap } from "../../components/mission-control/PortfolioThesisMap";
import { SystemStatusOverview } from "../../components/mission-control/SystemStatusOverview";
import { AuthorityCard } from "../../components/status/AuthorityCard";
import { errorMessage, isOpenTicket } from "../../lib/guards";
import { ledgerStatusMap, reconciliationStatusMap } from "../../lib/statusMap";

export function DashboardPage() {
  const health = useHealthQuery();
  const ledger = useLedgerStatusQuery();
  const snapshot = useLedgerSnapshotQuery();
  const reconciliation = useReconciliationQuery();
  const tickets = useTicketsQuery();
  const executions = useExecutionsQuery();
  const instruments = useInstrumentsQuery();
  const accounts = useAccountsQuery();
  const overrides = useOverrides();
  const postmortems = usePostmortemTasks({ status: "scheduled" });
  const recentReports = useReports({ limit: 3 });
  const governance = useGovernanceOverview();
  const research = useResearchItems();
  const macro = useMacroItems();
  const seniorMemos = useSeniorMemos();
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);

  const errors = [
    health.error,
    ledger.error,
    snapshot.error,
    reconciliation.error,
    tickets.error,
    executions.error,
    instruments.error,
    accounts.error,
    overrides.error,
    postmortems.error,
    recentReports.error,
    governance.error,
    research.error,
    macro.error,
    seniorMemos.error,
  ].filter(Boolean);

  const ledgerDef = ledger.data ? ledgerStatusMap[ledger.data.ledger_status] : { label: "확인 중", tone: "gray" as const, description: "API 응답 대기" };
  const reconKey = reconciliation.data?.reconciliation?.reconciliation_status ?? "none";
  const reconDef = reconciliationStatusMap[reconKey];
  const openCount = tickets.data?.tickets.filter(isOpenTicket).length ?? 0;
  const pendingExecutionCount = executions.data?.count ?? 0;
  const openOverrideCount = overrides.data?.open_count ?? 0;
  const pendingPostmortemCount = postmortems.data?.count ?? 0;
  const governanceWarningCount = governance.data?.stale_context_warnings.length ?? 0;
  const contextRecordCount = (research.data?.count ?? 0) + (macro.data?.count ?? 0) + (seniorMemos.data?.count ?? 0);

  return (
    <div className="page dashboard-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">PORTFOLIO OS MISSION CONTROL</p>
          <h1>Mission Control Dashboard</h1>
          <p>Portfolio OS는 자동매매 시스템이 아닙니다.</p>
          <p>장부 상태, Risk Engine, 수동 승인, 정산 증거가 각각의 권한 경계를 갖습니다.</p>
          <p>이 화면은 판단 보조와 감사용 Mission Control입니다.</p>
        </div>
        <span className="read-only-tag">NO DIRECT TRADING</span>
      </header>

      {errors.length > 0 ? (
        <div className="inline-error" role="alert">
          <strong>일부 시스템 데이터를 읽지 못했습니다.</strong>
          <span>{errorMessage(errors[0])}</span>
        </div>
      ) : null}

      {runtime.source === "mock" ? (
        <section className="panel api-unavailable-panel" aria-label="API unavailable helper">
          <div>
            <p className="eyebrow">API SOURCE</p>
            <h2>Mock fallback is active</h2>
            <p>FastAPI에 연결할 수 없어 UI 검증용 샘플 데이터가 표시됩니다. 실제 포트폴리오 상태가 아니며 mutation 버튼은 비활성화됩니다.</p>
          </div>
          <code>python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8000</code>
        </section>
      ) : null}

      <section className="authority-grid dashboard-authority-grid" aria-label="Authority status cards">
        <AuthorityCard icon={ShieldCheck} label="LEDGER STATUS" value={ledgerDef.label} detail={ledgerDef.description} tone={ledgerDef.tone} />
        <AuthorityCard icon={Activity} label="LATEST RECONCILIATION" value={reconDef.label} detail={reconciliation.data?.reconciliation?.as_of_date ?? "기록 없음"} tone={reconDef.tone} />
        <AuthorityCard icon={ClipboardList} label="OPEN TICKETS" value={openCount} detail="validated / approved" tone={openCount ? "amber" : "green"} />
        <AuthorityCard icon={Hourglass} label="PENDING EXECUTIONS" value={pendingExecutionCount} detail="정산 확정 대기" tone={pendingExecutionCount > 0 ? "amber" : "green"} to="/executions" />
        <AuthorityCard icon={Workflow} label="OPEN OVERRIDES" value={openOverrideCount} detail="declared exception" tone={openOverrideCount ? "red" : "green"} to="/overrides" />
        <AuthorityCard icon={BookOpenText} label="POSTMORTEMS" value={pendingPostmortemCount} detail="scheduled reviews" tone={pendingPostmortemCount ? "amber" : "green"} to="/postmortems" />
        <AuthorityCard icon={Database} label="API SOURCE" value={runtime.source === "mock" ? "MOCK" : "LIVE"} detail={runtime.source === "mock" ? "sample fallback" : health.data?.app_mode ?? "연결 중"} tone={runtime.source === "mock" ? "amber" : health.data?.database_ready ? "green" : "red"} />
        <AuthorityCard icon={Gauge} label="CONTEXT HEALTH" value={governanceWarningCount ? `${governanceWarningCount} WARN` : "READY"} detail={governance.data?.context_package_status ? "context package present" : "no context package"} tone={governanceWarningCount ? "amber" : "green"} to="/governance" />
        <AuthorityCard icon={BrainCircuit} label="INTELLIGENCE" value={contextRecordCount} detail={`${research.data?.count ?? 0} research / ${macro.data?.count ?? 0} macro / ${seniorMemos.data?.count ?? 0} memos`} tone={contextRecordCount ? "cyan" : "gray"} to="/research" />
      </section>

      <section className="panel safety-strip" aria-label="System boundaries">
        <div><strong>No broker integration</strong><span>브로커 쓰기 API 없음</span></div>
        <div><strong>No automatic trading</strong><span>자동 주문/실행 없음</span></div>
        <div><strong>Risk Engine authority</strong><span>공식 티켓 경로 유지</span></div>
        <div><strong>Reconciliation boundary</strong><span>수동 실행은 정산으로 확정</span></div>
        <Link className="table-link" to="/system">전체 경계 보기</Link>
      </section>

      <section className="panel recent-reports-panel">
        <div className="panel__header"><div><p className="eyebrow">RECENT REPORTS</p><h2>최근 리포트</h2></div><Link className="table-link" to="/reports">리포트 센터</Link></div>
        {(recentReports.data?.reports ?? []).length === 0 ? (
          <div className="empty-state"><span>NO REPORTS</span><p>표시할 보고서가 없습니다.</p></div>
        ) : (
          <ol className="recent-report-list">
            {recentReports.data!.reports.map((report) => (
              <li key={report.report_reference}>
                <FileText aria-hidden="true" />
                <div><Link to={`/reports?reference=${encodeURIComponent(report.report_reference)}`}>{report.title}</Link><span>{report.category} · {report.format}</span></div>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="panel context-summary-panel">
        <div className="panel__header"><div><p className="eyebrow">CONTEXT SUMMARY</p><h2>리서치 / 매크로 / 메모</h2></div><Link className="table-link" to="/governance">거버넌스</Link></div>
        <div className="context-summary-grid">
          <Link to="/research"><FileText aria-hidden="true" /><strong>{research.data?.count ?? 0}</strong><span>Research packets</span></Link>
          <Link to="/macro"><Gauge aria-hidden="true" /><strong>{macro.data?.count ?? 0}</strong><span>Macro contexts</span></Link>
          <Link to="/senior-memos"><BrainCircuit aria-hidden="true" /><strong>{seniorMemos.data?.count ?? 0}</strong><span>Senior memos</span></Link>
        </div>
      </section>

      <div className="dashboard-grid">
        <PortfolioThesisMap positions={snapshot.data?.positions ?? []} />
        <SystemStatusOverview health={health.data} ledger={ledger.data} reconciliation={reconciliation.data} />
        <AlertsPanel health={health.data} ledger={ledger.data} reconciliation={reconciliation.data} executions={executions.data} overrides={overrides.data} postmortems={postmortems.data} isMock={runtime.source === "mock"} />
        <PendingActionsPanel postmortems={postmortems.data} />
        <ActivityTimeline reconciliation={reconciliation.data} tickets={tickets.data} executions={executions.data} overrides={overrides.data} journal={undefined} />
        <OpenTicketsPanel tickets={tickets.data} instruments={instruments.data} />
      </div>
    </div>
  );
}
