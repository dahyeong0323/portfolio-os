import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { DashboardPage } from "./DashboardPage";

describe("DashboardPage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("backend offline")));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the final Mission Control dashboard with visible authority boundaries and mock fallback state", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Mission Control Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Portfolio OS는 자동매매 시스템이 아닙니다.")).toBeInTheDocument();
    expect(screen.getByText("이 화면은 판단 보조와 감사용 Mission Control입니다.")).toBeInTheDocument();
    expect(await screen.findByText("Mock fallback is active")).toBeInTheDocument();
    expect(await screen.findByText("DEMO-ALPHA")).toBeInTheDocument();
    expect(screen.getByText("No broker integration")).toBeInTheDocument();
    expect(screen.getByText("Risk Engine authority")).toBeInTheDocument();
    expect(screen.getAllByText("CONTEXT HEALTH").length).toBeGreaterThan(0);

    const forbidden = new RegExp([["Buy", "Now"].join(" "), ["Sell", "Now"].join(" "), ["Quick", "Trade"].join(" "), "즉시 매수", "즉시 매도"].join("|"), "i");
    expect(screen.queryAllByRole("button", { name: forbidden })).toHaveLength(0);
  });
});
