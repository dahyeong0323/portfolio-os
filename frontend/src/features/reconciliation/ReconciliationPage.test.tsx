import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { mockAccounts, mockReconciliation } from "../../api/mocks/mockData";
import type { ReconciliationSnapshot } from "../../api/types";
import { ReconciliationPage } from "./ReconciliationPage";
import { ReconciliationDiffViewer } from "./components/ReconciliationDiffViewer";
import { ReconciliationReportViewer } from "./components/ReconciliationReportViewer";

const emptyLatest = { found: false, reconciliation: null };
const importResponse = {
  artifact_id: "00000000-0000-4000-8000-000000000001",
  account_id: 9001,
  source: "csv_import",
  as_of_date: "2026-06-15",
  status: "imported" as const,
  counts: { positions: 1, cash: 1, liabilities: 0, tax_reserves: 0 },
  warnings: [],
  imported_at: "2026-06-15T08:00:00Z",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <ReconciliationPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function baseFetch(extra?: (url: string, init?: RequestInit) => Response | undefined) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const override = extra?.(url, init);
    if (override) return override;
    if (url === "/api/v1/accounts") return json(mockAccounts);
    if (url === "/api/v1/reconciliations/latest") return json(emptyLatest);
    throw new Error(`Unhandled request: ${init?.method ?? "GET"} ${url}`);
  });
}

afterEach(() => cleanup());

async function uploadCashCsv(user: ReturnType<typeof userEvent.setup>) {
  await waitFor(() => expect(screen.getByLabelText(/대상 계좌/)).toHaveValue("9001"));
  const file = new File(["currency,amount\nUSD,10000\n"], "cash.csv", { type: "text/csv" });
  await user.upload(screen.getByLabelText(/현금 CSV/), file);
  await user.click(screen.getByRole("button", { name: "스냅샷 가져오기" }));
}

describe("ReconciliationPage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders the operational wizard initial state and authority boundaries", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderPage();
    expect(screen.getByRole("heading", { name: "정산" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "스냅샷 가져오기" })).toBeEnabled());
    expect(screen.getByText("거래 승인 아님")).toBeInTheDocument();
    expect(screen.getByText(/cash_balances/)).toBeInTheDocument();
  });

  it("shows the imported artifact summary", async () => {
    vi.stubGlobal("fetch", baseFetch((url, init) => {
      if (url === "/api/v1/snapshots/external-imports" && init?.method === "POST") return json(importResponse, 201);
    }));
    const user = userEvent.setup();
    renderPage();
    await uploadCashCsv(user);
    expect(await screen.findByRole("heading", { name: "가져오기 결과 확인" })).toBeInTheDocument();
    const summary = screen.getByRole("heading", { name: "가져오기 결과 확인" }).closest("section")!;
    expect(within(summary).getByText("포지션")).toBeInTheDocument();
    expect(within(summary).getByRole("button", { name: "정산 실행" })).toBeEnabled();
  });

  it("runs reconciliation and renders non-empty over-tolerance differences", async () => {
    const detail: ReconciliationSnapshot = {
      ...mockReconciliation.reconciliation!,
      reconciliation_id: 42,
      reconciliation_status: "failed",
      ledger_status_after: "broken",
      cash_differences: [{ account_id: 9001, currency: "USD", expected_amount: "10000", actual_amount: "9800", difference: "-200", within_tolerance: false }],
    };
    vi.stubGlobal("fetch", baseFetch((url, init) => {
      if (url === "/api/v1/snapshots/external-imports" && init?.method === "POST") return json(importResponse, 201);
      if (url === "/api/v1/reconciliations" && init?.method === "POST") return json({ reconciliation_id: 42, reconciliation_status: "failed", ledger_status: "broken", generated_at: "2026-06-15T08:01:00Z", diff_counts: { positions: 0, cash: 1, liabilities: 0, tax_reserves: 0 }, report_available: true, report_reference: "reconciliation:42:markdown", explanation: "One or more differences exceed the allowed tolerance.", warnings: [] }, 201);
      if (url === "/api/v1/reconciliations/42") return json(detail);
    }));
    const user = userEvent.setup();
    renderPage();
    await uploadCashCsv(user);
    await user.click(await screen.findByRole("button", { name: "정산 실행" }));
    expect(await screen.findByText("One or more differences exceed the allowed tolerance.")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "차이 검토" })).toBeInTheDocument();
    expect(screen.getByText("-200")).toBeInTheDocument();
    expect(screen.getByText("초과")).toBeInTheDocument();
  });

  it("shows structured import errors near the active step", async () => {
    vi.stubGlobal("fetch", baseFetch((url, init) => {
      if (url === "/api/v1/snapshots/external-imports" && init?.method === "POST") return json({ error: { code: "invalid_snapshot_headers", message: "Cash CSV headers are invalid.", details: null } }, 422);
    }));
    const user = userEvent.setup();
    renderPage();
    await uploadCashCsv(user);
    expect(await screen.findByRole("alert")).toHaveTextContent("Cash CSV headers are invalid.");
  });

  it("disables real reconciliation controls after network fallback enters mock mode", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderPage();
    await waitFor(() => expect(screen.getByRole("button", { name: "스냅샷 가져오기" })).toBeDisabled());
    expect(screen.getByText(/Mock mode에서는 실제 파일 업로드/)).toBeInTheDocument();
  });
});

describe("ReconciliationDiffViewer", () => {
  it("renders clean empty sections", () => {
    const detail = { ...mockReconciliation.reconciliation!, position_differences: [], cash_differences: [], liability_differences: [], tax_reserve_differences: [] };
    render(<ReconciliationDiffViewer reconciliation={detail} />);
    expect(screen.getByText("현금 차이가 없습니다.")).toBeInTheDocument();
  });

  it("surfaces unresolved instruments instead of hiding them", () => {
    const detail = { ...mockReconciliation.reconciliation!, actual_positions: [{ account_id: 1, symbol: "DEMO-MISSING", currency: "USD", quantity: "1", exchange: null, instrument_id: null, match_status: "missing", match_error: "no match" }] };
    render(<ReconciliationDiffViewer reconciliation={detail} />);
    expect(screen.getByText("매칭되지 않은 종목")).toBeInTheDocument();
    expect(screen.getByText(/DEMO-MISSING/)).toBeInTheDocument();
  });
});

describe("ReconciliationReportViewer", () => {
  it("renders report HTML-like content as inert text", () => {
    render(<ReconciliationReportViewer requested available report={{ reconciliation_id: 1, format: "markdown", content: "<img src=x onerror=alert(1)>", generated_at: "2026-06-15T08:00:00Z", report_reference: "demo" }} pending={false} error={null} onRequest={() => undefined} />);
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });
});
