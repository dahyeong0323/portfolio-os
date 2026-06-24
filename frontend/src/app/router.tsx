import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { GovernancePage, MacroPage, ResearchPage, SeniorMemosPage } from "../features/context-explorer/ContextExplorerPages";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { PendingExecutionsPage } from "../features/executions/PendingExecutionsPage";
import { JournalDetailPage } from "../features/journal/JournalDetailPage";
import { JournalPage } from "../features/journal/JournalPage";
import { LedgerPage } from "../features/ledger/LedgerPage";
import { OverrideDetailPage } from "../features/overrides/OverrideDetailPage";
import { OverridesPage } from "../features/overrides/OverridesPage";
import { PostmortemsPage } from "../features/postmortems/PostmortemsPage";
import { ReconciliationPage } from "../features/reconciliation/ReconciliationPage";
import { ReportsPage } from "../features/reports/ReportsPage";
import { RiskWorkspacePage } from "../features/risk/RiskWorkspacePage";
import { NotFoundPage } from "../features/system/NotFoundPage";
import { RouteErrorPage } from "../features/system/RouteErrorPage";
import { SystemPage } from "../features/system/SystemPage";
import { TicketDetailPage } from "../features/tickets/TicketDetailPage";
import { TicketsPage } from "../features/tickets/TicketsPage";

export const router = createBrowserRouter(
  [{ path: "/", element: <AppShell />, errorElement: <RouteErrorPage />, children: [
    { index: true, element: <DashboardPage /> },
    { path: "ledger", element: <LedgerPage /> },
    { path: "reconciliation", element: <ReconciliationPage /> },
    { path: "risk", element: <RiskWorkspacePage /> },
    { path: "tickets", element: <TicketsPage /> },
    { path: "tickets/:ticketId", element: <TicketDetailPage /> },
    { path: "executions", element: <PendingExecutionsPage /> },
    { path: "overrides", element: <OverridesPage /> },
    { path: "overrides/:overrideId", element: <OverrideDetailPage /> },
    { path: "journal", element: <JournalPage /> },
    { path: "journal/:journalId", element: <JournalDetailPage /> },
    { path: "postmortems", element: <PostmortemsPage /> },
    { path: "reports", element: <ReportsPage /> },
    { path: "research", element: <ResearchPage /> },
    { path: "research/:researchId", element: <ResearchPage /> },
    { path: "macro", element: <MacroPage /> },
    { path: "macro/:macroId", element: <MacroPage /> },
    { path: "senior-memos", element: <SeniorMemosPage /> },
    { path: "senior-memos/:memoId", element: <SeniorMemosPage /> },
    { path: "governance", element: <GovernancePage /> },
    { path: "system", element: <SystemPage /> },
    { path: "*", element: <NotFoundPage /> },
  ]}],
  { future: { v7_relativeSplatPath: true } },
);
