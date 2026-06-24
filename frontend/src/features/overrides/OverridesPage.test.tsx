import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { mockAccounts, mockInstruments, mockJournal, mockOverrideDetail, mockOverrides, mockPostmortems } from "../../api/mocks/mockData";
import { JournalPage } from "../journal/JournalPage";
import { PostmortemsPage } from "../postmortems/PostmortemsPage";
import { OverrideDetailPage } from "./OverrideDetailPage";
import { OverridesPage } from "./OverridesPage";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderWithClient(element: ReactElement, initialEntries = ["/"]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        {element}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function baseFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/overrides" && init?.method === "POST") return json(mockOverrideDetail, 201);
    if (url === "/api/v1/overrides") return json(mockOverrides);
    if (url === "/api/v1/overrides/97001") return json(mockOverrideDetail);
    if (url.startsWith("/api/v1/journal")) return json(mockJournal);
    if (url.startsWith("/api/v1/postmortems")) return json(mockPostmortems);
    if (url === "/api/v1/accounts") return json(mockAccounts);
    if (url === "/api/v1/instruments") return json(mockInstruments);
    throw new Error(`Unhandled request: ${init?.method ?? "GET"} ${url}`);
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Stage 7 override and journal UI", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders open and historical overrides", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderWithClient(<OverridesPage />);
    expect(await screen.findByRole("heading", { name: "오버라이드" })).toBeInTheDocument();
    expect(await screen.findByText("#OVR-97001")).toBeInTheDocument();
    expect(screen.getByText("공식 Risk Engine 검증 흐름이 아닌, 명시적 예외 선언과 감사 기록입니다.")).toBeInTheDocument();
  });

  it("requires a human reason before declaring override", async () => {
    vi.stubGlobal("fetch", baseFetch());
    const user = userEvent.setup();
    renderWithClient(<OverridesPage />);
    await screen.findByRole("heading", { name: "오버라이드" });
    const submit = screen.getByRole("button", { name: "오버라이드 선언" });
    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText("인간 사유"), "테스트 예외 사유");
    expect(submit).toBeEnabled();
  });

  it("disables override mutation in mock mode", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderWithClient(<OverridesPage />);
    expect(await screen.findByText(/MOCK MODE에서는 오버라이드 선언/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "오버라이드 선언" })).toBeDisabled();
  });

  it("renders override detail warning, linked journal, and postmortem status", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderWithClient(
      <Routes><Route path="/overrides/:overrideId" element={<OverrideDetailPage />} /></Routes>,
      ["/overrides/97001"],
    );
    expect(await screen.findByRole("heading", { name: "오버라이드 #97001" })).toBeInTheDocument();
    expect(await screen.findByText("공식 Risk 검증 흐름이 아닙니다")).toBeInTheDocument();
    expect(screen.getAllByText("결정 저널").length).toBeGreaterThan(0);
    expect(screen.getByText("복기 태스크")).toBeInTheDocument();
  });

  it("renders journal and postmortem pages", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderWithClient(<JournalPage />);
    expect(await screen.findByRole("heading", { name: "저널 / 복기" })).toBeInTheDocument();
    expect(await screen.findByText("override_declared")).toBeInTheDocument();
    cleanup();
    renderWithClient(<PostmortemsPage />);
    expect(await screen.findByRole("heading", { name: "복기 태스크" })).toBeInTheDocument();
    expect(await screen.findByText("#PM-96001")).toBeInTheDocument();
  });

  it("renders structured API errors visibly", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/v1/overrides") return json({ error: { code: "override_declare_blocked", message: "override blocked", details: null } }, 409);
      if (url === "/api/v1/accounts") return json(mockAccounts);
      if (url === "/api/v1/instruments") return json(mockInstruments);
      return json({});
    }));
    renderWithClient(<OverridesPage />);
    await waitFor(() => expect(screen.getByText("override blocked")).toBeInTheDocument());
  });
});
