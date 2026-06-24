import type { ErrorEnvelope } from "./types";

export type MockKey =
  | "health"
  | "ledgerStatus"
  | "ledgerSnapshot"
  | "accounts"
  | "instruments"
  | "reconciliation"
  | "reconciliationById"
  | "reconciliationReport"
  | "reportCategories"
  | "reports"
  | "reportDetail"
  | "researchItems"
  | "researchDetail"
  | "macroItems"
  | "macroDetail"
  | "seniorMemos"
  | "seniorMemoDetail"
  | "governanceOverview"
  | "governanceEvents"
  | "tickets"
  | "ticketDetail"
  | "riskValidation"
  | "executions"
  | "executionDetail"
  | "overrides"
  | "overrideDetail"
  | "journal"
  | "journalDetail"
  | "postmortems";
export type ApiSource = "live" | "mock";

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number | null = null,
    public readonly details: unknown = null,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

type SourceSnapshot = { source: ApiSource; reason: string | null; generation: number };

let sourceSnapshot: SourceSnapshot = {
  source: import.meta.env.VITE_USE_MOCKS === "true" ? "mock" : "live",
  reason: import.meta.env.VITE_USE_MOCKS === "true" ? "VITE_USE_MOCKS=true" : null,
  generation: 0,
};
const listeners = new Set<() => void>();

function publish(source: ApiSource, reason: string | null): void {
  if (sourceSnapshot.source === source && sourceSnapshot.reason === reason) return;
  sourceSnapshot = { source, reason, generation: sourceSnapshot.generation + 1 };
  listeners.forEach((listener) => listener());
}

export const apiRuntime = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  getSnapshot() {
    return sourceSnapshot;
  },
  retryLive() {
    publish("live", null);
  },
};

export function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (!value || typeof value !== "object" || !("error" in value)) return false;
  const error = (value as { error?: unknown }).error;
  return Boolean(error && typeof error === "object" && "code" in error && "message" in error);
}

function isNetworkFailure(error: unknown): boolean {
  return (
    error instanceof TypeError ||
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof ApiClientError && error.code === "dev_proxy_unavailable")
  );
}

function networkReason(error: unknown): string {
  return error instanceof DOMException && error.name === "AbortError"
    ? "API 응답 시간이 초과되었습니다."
    : "FastAPI 서버에 연결할 수 없습니다.";
}

async function parseError(response: Response): Promise<ApiClientError> {
  const rawBody = await response.text();
  let body: unknown = null;
  try {
    body = rawBody ? JSON.parse(rawBody) : null;
  } catch {
    body = null;
  }
  if (isErrorEnvelope(body)) {
    return new ApiClientError(body.error.code, body.error.message, response.status, body.error.details);
  }
  if (response.status === 500 && rawBody.trim() === "") {
    return new ApiClientError("dev_proxy_unavailable", "Vite 개발 프록시가 FastAPI에 연결하지 못했습니다.", response.status);
  }
  return new ApiClientError("http_error", `API 요청이 실패했습니다. (${response.status})`, response.status);
}

export async function apiGet<T>(path: string, mockKey: MockKey): Promise<T> {
  if (sourceSnapshot.source === "mock") {
    const { getMockResponse } = await import("./mocks/mockClient");
    return getMockResponse<T>(mockKey);
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 3500);
  try {
    const response = await fetch(path, { headers: { Accept: "application/json" }, signal: controller.signal });
    if (!response.ok) throw await parseError(response);
    publish("live", null);
    return (await response.json()) as T;
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    const reason = networkReason(error);
    publish("mock", reason);
    const { getMockResponse } = await import("./mocks/mockClient");
    return getMockResponse<T>(mockKey);
  } finally {
    window.clearTimeout(timeout);
  }
}

async function apiMutation<T>(path: string, init: RequestInit): Promise<T> {
  if (sourceSnapshot.source === "mock") {
    throw new ApiClientError("mock_mode_write_disabled", "Mock mode에서는 실제 쓰기 API를 사용할 수 없습니다.");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20_000);
  try {
    const response = await fetch(path, { ...init, signal: controller.signal });
    if (!response.ok) throw await parseError(response);
    publish("live", null);
    return (await response.json()) as T;
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    const reason = networkReason(error);
    publish("mock", reason);
    throw new ApiClientError("network_unavailable", `${reason} 작업은 실행되지 않았습니다.`, null);
  } finally {
    window.clearTimeout(timeout);
  }
}

export function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  return apiMutation<T>(path, {
    method: "POST",
    headers: { Accept: "application/json" },
    body: formData,
  });
}

export function apiPostJson<TResponse, TRequest>(path: string, payload: TRequest): Promise<TResponse> {
  return apiMutation<TResponse>(path, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
