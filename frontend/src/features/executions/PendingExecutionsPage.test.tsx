import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { mockExecutions, mockReconciliation } from "../../api/mocks/mockData";
import type { ConfirmExecutionsResponse, PendingExecutionListResponse } from "../../api/types";
import { PendingExecutionsPage } from "./PendingExecutionsPage";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderWithClient(element: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        {element}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const confirmationResult: ConfirmExecutionsResponse = {
  confirmation_run_id: "stage6-test",
  reconciliation_id_used: 9901,
  total_pending_checked: 1,
  confirmed_execution_ids: [9501],
  still_pending_execution_ids: [],
  failed_execution_ids: [],
  skipped_executions: [],
  explanation: "Checked against passed reconciliation evidence.",
};

function baseFetch(pending: PendingExecutionListResponse = mockExecutions, confirmStatus = 200) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/executions/pending") return json(pending);
    if (url === "/api/v1/reconciliations/latest") return json(mockReconciliation);
    if (url === "/api/v1/executions/confirm-after-reconciliation" && init?.method === "POST") {
      if (confirmStatus >= 400) {
        return json({ error: { code: "confirmation_blocked", message: "passed reconciliation evidence required", details: null } }, confirmStatus);
      }
      return json(confirmationResult);
    }
    throw new Error(`Unhandled request: ${init?.method ?? "GET"} ${url}`);
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PendingExecutionsPage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders empty state for no pending executions", async () => {
    vi.stubGlobal("fetch", baseFetch({ count: 0, executions: [] }));
    renderWithClient(<PendingExecutionsPage />);
    expect(await screen.findByRole("heading", { name: "실행 기록 정산 확인" })).toBeInTheDocument();
    expect(screen.getByText("정산을 기다리는 수동 실행 기록이 없습니다.")).toBeInTheDocument();
  });

  it("renders pending execution rows and eligible confirmation action", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderWithClient(<PendingExecutionsPage />);
    expect(await screen.findByText("#9501")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "정산 증거로 확정" })).toBeEnabled();
    expect(screen.getByText("confirmed")).toBeInTheDocument();
  });

  it("disables confirmation mutation controls in mock mode", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderWithClient(<PendingExecutionsPage />);
    expect(await screen.findByText(/MOCK MODE에서는 실행 기록 확정을 만들 수 없습니다/)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "정산 증거로 확정" })).toBeDisabled();
  });

  it("displays successful confirmation result groups", async () => {
    vi.stubGlobal("fetch", baseFetch());
    const user = userEvent.setup();
    renderWithClient(<PendingExecutionsPage />);
    await user.click(await screen.findByRole("button", { name: "정산 증거로 확정" }));
    expect(await screen.findByText("stage6-test")).toBeInTheDocument();
    expect(screen.getByText("Confirmed")).toBeInTheDocument();
    expect(screen.getByText("9501")).toBeInTheDocument();
  });

  it("renders structured confirmation errors visibly", async () => {
    vi.stubGlobal("fetch", baseFetch(mockExecutions, 409));
    const user = userEvent.setup();
    renderWithClient(<PendingExecutionsPage />);
    await user.click(await screen.findByRole("button", { name: "정산 증거로 확정" }));
    await waitFor(() => expect(screen.getByText("passed reconciliation evidence required")).toBeInTheDocument());
  });
});
