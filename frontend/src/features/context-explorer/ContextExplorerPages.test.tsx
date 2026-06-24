import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import type {
  GovernanceEventListResponse,
  GovernanceOverviewResponse,
  MacroListResponse,
  ResearchDetailResponse,
  ResearchListResponse,
  SeniorMemoListResponse,
} from "../../api/types";
import { GovernancePage, MacroPage, ResearchPage, SeniorMemosPage } from "./ContextExplorerPages";

const researchList: ResearchListResponse = {
  count: 1,
  items: [{
    research_id: 9001,
    report_reference: "DEMO-RESEARCH-9001",
    title: "[샘플] Research sample",
    subject: "<img src=x onerror=alert(1)>",
    instrument: "DEMO-ALPHA",
    thesis: "[샘플] thesis",
    status: "complete",
    created_at: "2026-06-14T08:10:00Z",
    updated_at: "2026-06-14T08:15:00Z",
    linked_report_reference: "DEMO-REPORT-STAGE-8",
    anti_thesis_present: true,
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

const researchDetail: ResearchDetailResponse = {
  metadata: { id: 9001, summary: "<script>alert(1)</script>" },
  thesis: { title: "[샘플] thesis" },
  anti_thesis: { present: true },
  sources: [{ title: "DEMO source" }],
  evidence_summary: { fact_count: 2 },
  linked_reports: ["DEMO-REPORT-STAGE-8", "../secret.md"],
  read_only_explanation: "Research context is read-only evidence. It is not order authority.",
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

const macroList: MacroListResponse = {
  count: 1,
  items: [{
    macro_id: 9101,
    report_reference: "DEMO-MACRO-9101",
    title: "[샘플] Macro sample",
    regime: "demo",
    scenario: "sample scenario",
    tags: ["DEMO-tag"],
    created_at: "2026-06-14T08:12:00Z",
    linked_report_reference: "DEMO-REPORT-STAGE-8",
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

const seniorMemos: SeniorMemoListResponse = {
  count: 1,
  memos: [{
    memo_id: 9201,
    report_reference: "DEMO-MEMO-9201",
    title: "[샘플] Senior memo",
    linked_intent_id: 1,
    ticket_id: 2,
    risk_validation_id: 3,
    recommendation_summary: "Context only",
    created_at: "2026-06-14T08:18:00Z",
    linked_report_reference: "../secret.md",
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

const governanceOverview: GovernanceOverviewResponse = {
  context_package_status: null,
  canary: null,
  health: null,
  stale_context_warnings: [],
  governance_report_references: ["DEMO-REPORT-STAGE-8"],
  canary_report_references: [],
  health_report_references: [],
  context_report_references: [],
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

const governanceEvents: GovernanceEventListResponse = { count: 0, events: [] };

function json(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

function stubFetch(overrides: Partial<Record<string, unknown>> = {}) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/v1/research") return json(overrides.researchList ?? researchList);
    if (url === "/api/v1/research/9001") return json(researchDetail);
    if (url === "/api/v1/macro") return json(overrides.macroList ?? macroList);
    if (url === "/api/v1/senior-memos") return json(overrides.seniorMemos ?? seniorMemos);
    if (url === "/api/v1/governance") return json(overrides.governanceOverview ?? governanceOverview);
    if (url === "/api/v1/governance/events") return json(overrides.governanceEvents ?? governanceEvents);
    throw new Error(`Unhandled request: ${url}`);
  });
}

function renderRoutes(initialEntry: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/research/:researchId" element={<ResearchPage />} />
          <Route path="/macro" element={<MacroPage />} />
          <Route path="/senior-memos" element={<SeniorMemosPage />} />
          <Route path="/governance" element={<GovernancePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => cleanup());

describe("ContextExplorerPages", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders research list and detail content as inert text", async () => {
    vi.stubGlobal("fetch", stubFetch());
    renderRoutes("/research/9001");
    expect(await screen.findByText("[샘플] Research sample")).toBeInTheDocument();
    await waitFor(() => expect(document.querySelector("pre")?.textContent).toContain("<script>alert(1)</script>"));
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getAllByRole("link", { name: /DEMO-REPORT-STAGE-8/ })[0]).toHaveAttribute("href", "/reports?reference=DEMO-REPORT-STAGE-8");
    expect(document.body.textContent).not.toContain("../secret.md");
  });

  it("renders clean empty states for empty research and governance events", async () => {
    vi.stubGlobal("fetch", stubFetch({ researchList: { count: 0, items: [] }, governanceEvents: { count: 0, events: [] } }));
    renderRoutes("/research");
    expect(await screen.findByText("표시할 Research context가 없습니다.")).toBeInTheDocument();
    cleanup();
    renderRoutes("/governance");
    expect(await screen.findByText("표시할 governance event가 없습니다.")).toBeInTheDocument();
  });

  it("renders macro and senior memo samples with authority warnings", async () => {
    vi.stubGlobal("fetch", stubFetch());
    const macro = renderRoutes("/macro");
    expect(await screen.findByText("[샘플] Macro sample")).toBeInTheDocument();
    expect(macro.container.textContent).toContain("Risk path remains upstream");
    cleanup();
    renderRoutes("/senior-memos");
    expect(await screen.findByText("[샘플] Senior memo")).toBeInTheDocument();
    expect(screen.queryByText("../secret.md")).not.toBeInTheDocument();
  });

  it("does not expose direct-trade command copy", async () => {
    vi.stubGlobal("fetch", stubFetch());
    const { container } = renderRoutes("/governance");
    await screen.findByText("Context health");
    const text = container.textContent ?? "";
    expect(text).not.toContain("Buy Now");
    expect(text).not.toContain("Sell Now");
    expect(text).not.toContain("Quick Trade");
    expect(text).not.toContain("즉시 매수");
    expect(text).not.toContain("즉시 매도");
  });
});
