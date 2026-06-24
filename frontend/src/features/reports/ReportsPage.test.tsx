import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import type { ReportCategoryListResponse, ReportDetailResponse, ReportListResponse } from "../../api/types";
import { ReportsPage } from "./ReportsPage";

const categories: ReportCategoryListResponse = {
  categories: [
    { category_id: "reconciliation", label: "정산 리포트", description: "Reconciliation reports", report_count: 1, supported_formats: ["markdown", "json"], latest_generated_at: "2026-06-14T07:45:00Z" },
    { category_id: "senior_memo", label: "시니어 메모", description: "Senior memo reports", report_count: 0, supported_formats: ["markdown", "json"], latest_generated_at: null },
  ],
};

const list: ReportListResponse = {
  count: 1,
  reports: [{
    report_reference: "report_eyJjIjoicmVjb25jaWxpYXRpb24iLCJmIjoicmVjb25jaWxpYXRpb25fNy5tZCJ9",
    category: "reconciliation",
    title: "정산 리포트 #7",
    format: "markdown",
    generated_at: "2026-06-14T07:45:00Z",
    linked_object_type: "reconciliation",
    linked_object_id: "7",
    safe_summary: "Reconciliation Report",
    available_actions: ["view", "copy", "download"],
    blocked_actions: ["broker_write", "automatic_execution"],
  }],
};

const detail: ReportDetailResponse = {
  ...list.reports[0]!,
  content: "# Reconciliation Report\n\n<img src=x onerror=alert(1)>\n",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderPage(initialEntries = ["/reports"]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <ReportsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function stubReportsFetch(reports: ReportListResponse = list) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/v1/reports/categories") return json(categories);
    if (url.startsWith("/api/v1/reports?")) {
      if (url.includes("category=senior_memo")) return json({ count: 0, reports: [] });
      return json(reports);
    }
    if (url === `/api/v1/reports/${encodeURIComponent(list.reports[0]!.report_reference)}`) return json(detail);
    throw new Error(`Unhandled request: ${url}`);
  });
}

afterEach(() => cleanup());

describe("ReportsPage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
    Object.defineProperty(navigator, "clipboard", { value: { writeText: vi.fn() }, configurable: true });
  });

  it("renders categories and report list", async () => {
    vi.stubGlobal("fetch", stubReportsFetch());
    renderPage();
    expect(await screen.findByRole("heading", { name: "리포트 센터" })).toBeInTheDocument();
    expect(await screen.findByText("정산 리포트")).toBeInTheDocument();
    expect(await screen.findByText("정산 리포트 #7")).toBeInTheDocument();
  });

  it("shows a clean empty state for an empty category", async () => {
    vi.stubGlobal("fetch", stubReportsFetch());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: /시니어 메모/ }));
    expect(await screen.findByText("이 분류에는 표시할 보고서가 없습니다.")).toBeInTheDocument();
  });

  it("renders HTML-like report content as inert text", async () => {
    vi.stubGlobal("fetch", stubReportsFetch());
    renderPage();
    await waitFor(() => expect(document.querySelector("pre")?.textContent).toContain("<img src=x onerror=alert(1)>"));
    expect(document.querySelector("img")).toBeNull();
  });

  it("does not send path-like malicious report references from UI controls", async () => {
    const malicious: ReportListResponse = {
      count: 1,
      reports: [{ ...list.reports[0]!, report_reference: "../secret.md", title: "malicious path" }],
    };
    const fetchSpy = stubReportsFetch(malicious);
    vi.stubGlobal("fetch", fetchSpy);
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "malicious path" }));
    await waitFor(() => {
      expect(fetchSpy.mock.calls.some(([url]) => String(url).includes("secret"))).toBe(false);
    });
  });
});
