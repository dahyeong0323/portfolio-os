import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiGet, apiPostForm, apiPostJson, apiRuntime, isErrorEnvelope } from "./client";
import type { HealthResponse } from "./types";

describe("API client", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("recognizes the backend structured error envelope", () => {
    expect(isErrorEnvelope({ error: { code: "database_not_ready", message: "not ready", details: null } })).toBe(true);
    expect(isErrorEnvelope({ message: "wrong shape" })).toBe(false);
  });

  it("falls back to explicit fake data after a network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const result = await apiGet<HealthResponse>("/api/v1/health", "health");
    expect(result.app_mode).toBe("mock-sample-read-only");
    expect(apiRuntime.getSnapshot().source).toBe("mock");
    expect(apiRuntime.getSnapshot().reason).toContain("연결할 수 없습니다");
  });

  it("does not hide an HTTP server error behind mock data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: "database_not_ready", message: "not ready", details: null } }), { status: 503, headers: { "Content-Type": "application/json" } })));
    await expect(apiGet<HealthResponse>("/api/v1/health", "health")).rejects.toEqual(expect.objectContaining({ code: "database_not_ready", status: 503 }));
    expect(apiRuntime.getSnapshot().source).toBe("live");
  });

  it("treats Vite's empty proxy 500 as a network fallback", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 500 })));
    const result = await apiGet<HealthResponse>("/api/v1/health", "health");
    expect(result.app_mode).toBe("mock-sample-read-only");
    expect(apiRuntime.getSnapshot()).toEqual(expect.objectContaining({ source: "mock" }));
  });

  it("sends FormData without overriding its multipart content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ artifact_id: "demo" }), { status: 201, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    const formData = new FormData();
    formData.append("account_id", "1");
    await apiPostForm("/api/v1/snapshots/external-imports", formData);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/snapshots/external-imports",
      expect.objectContaining({ method: "POST", body: formData, headers: { Accept: "application/json" } }),
    );
  });

  it("does not convert a failed mutation into a fake success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(apiPostJson("/api/v1/reconciliations", { artifact_id: "x" })).rejects.toEqual(
      expect.objectContaining({ code: "network_unavailable" }),
    );
    expect(apiRuntime.getSnapshot().source).toBe("mock");
  });

  it("preserves structured FastAPI mutation errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ error: { code: "snapshot_date_mismatch", message: "date mismatch", details: null } }, 422)));
    await expect(apiPostJson("/api/v1/reconciliations", { artifact_id: "x" })).rejects.toEqual(
      expect.objectContaining({ code: "snapshot_date_mismatch", status: 422 }),
    );
    expect(apiRuntime.getSnapshot().source).toBe("live");
  });
});

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}
