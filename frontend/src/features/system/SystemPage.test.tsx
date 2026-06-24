import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { AppShell } from "../../components/layout/AppShell";
import { DashboardPage } from "../dashboard/DashboardPage";
import { NotFoundPage } from "./NotFoundPage";
import { SystemPage } from "./SystemPage";

function renderRoute(path: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [{ path: "/", element: <AppShell />, children: [
      { index: true, element: <DashboardPage /> },
      { path: "system", element: <SystemPage /> },
      { path: "*", element: <NotFoundPage /> },
    ]}],
    { initialEntries: [path], future: { v7_relativeSplatPath: true } },
  );
  return render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>);
}

describe("System boundaries routing", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the read-only system boundaries page and visible mock mode marker", async () => {
    renderRoute("/system");
    expect(await screen.findByRole("heading", { name: "Safety & Packaging Readiness" })).toBeInTheDocument();
    expect(await screen.findByText("MOCK MODE · 샘플 데이터")).toBeInTheDocument();
    expect(screen.getByText("No frontend SQLite access")).toBeInTheDocument();
    expect(screen.getByText("No CLI invocation")).toBeInTheDocument();
    expect(screen.getByText("Risk Engine remains authority")).toBeInTheDocument();
  });

  it("renders a clean 404 route fallback", () => {
    renderRoute("/missing-stage-10-route");
    expect(screen.getByText("404 ROUTE")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "요청한 Mission Control 화면을 찾을 수 없습니다." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /System boundaries/ })).toHaveAttribute("href", "/system");
  });
});
