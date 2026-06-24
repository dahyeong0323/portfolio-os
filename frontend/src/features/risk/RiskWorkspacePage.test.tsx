import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRuntime } from "../../api/client";
import { mockAccounts, mockInstruments, mockTicketDetail } from "../../api/mocks/mockData";
import type { CreateIntentResponse, CreateTicketResponse, ManualExecutionResponse, TicketActionResponse, ValidateIntentResponse } from "../../api/types";
import { TicketDetailPage } from "../tickets/TicketDetailPage";
import { RiskWorkspacePage } from "./RiskWorkspacePage";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const createdIntent: CreateIntentResponse = {
  intent: {
    intent_id: 321,
    account_id: 9001,
    instrument_id: 9101,
    intent_type: "buy",
    intent_source: "manual",
    requested_quantity: null,
    requested_notional: "500",
    limit_price: "100",
    currency: "USD",
    order_type: "limit",
    rationale: "test",
    status: "drafted",
    created_at: "2026-06-16T08:00:00Z",
    updated_at: "2026-06-16T08:00:00Z",
    expires_at: null,
  },
  next_available_actions: ["validate_risk"],
};

function validation(status: "passed" | "adjusted" | "rejected"): ValidateIntentResponse {
  return {
    validation: {
      risk_validation_id: 654,
      intent_id: 321,
      policy_version_id: 1,
      reconciliation_id: null,
      ledger_status_at_validation: status === "rejected" ? "provisional" : "reconciled",
      ledger_snapshot_as_of: "2026-06-16",
      ledger_snapshot_digest: "digest",
      validation_status: status,
      action_class: "risk_increasing",
      requested_quantity: null,
      requested_notional: "500",
      approved_quantity: status === "rejected" ? null : "5",
      approved_notional: status === "adjusted" ? "300" : status === "passed" ? "500" : null,
      max_allowed_notional: status === "adjusted" ? "300" : null,
      currency: "USD",
      cash_before: "10000",
      cash_after: "9500",
      tax_reserve_required: "0",
      checks: [
        { check_code: "LEDGER_STATUS_GATE", status: status === "rejected" ? "failed" : "passed", message: "ledger gate", threshold_value: null, observed_value: null, adjusted_value: null },
      ],
      failure_reasons: status === "rejected" ? ["LEDGER_STATUS_GATE"] : [],
      warnings: [],
      created_at: "2026-06-16T08:01:00Z",
      expires_at: "2026-06-17T08:01:00Z",
      is_superseded: false,
    },
    ledger_status_gate: { check_code: "LEDGER_STATUS_GATE", status: status === "rejected" ? "failed" : "passed", message: "ledger gate", threshold_value: null, observed_value: null, adjusted_value: null },
    failed_checks: status === "rejected" ? [{ check_code: "LEDGER_STATUS_GATE", status: "failed", message: "ledger gate failed", threshold_value: null, observed_value: null, adjusted_value: null }] : [],
    warnings: [],
    explanation: status === "passed" ? "Risk Engine validation passed." : status === "adjusted" ? "Risk Engine adjusted the allowed size." : "Risk Engine rejected the intent.",
    next_available_actions: status === "rejected" ? [] : ["create_ticket"],
  };
}

const createdTicket: CreateTicketResponse = {
  ticket: mockTicketDetail.ticket,
  risk_validation_id: 654,
  intent_id: 321,
  available_actions: ["approve_ticket", "reject_ticket"],
  blocked_actions: ["modify_deferred", "broker_write_not_available", "automatic_execution_not_available", "manual_execution_requires_approval"],
};

const approvedTicketDetail = {
  ...mockTicketDetail,
  ticket: {
    ...mockTicketDetail.ticket,
    status: "approved" as const,
    human_decision: "approved",
    human_decision_reason: "테스트 승인",
    approved_at: "2026-06-16T08:20:00Z",
    updated_at: "2026-06-16T08:20:00Z",
  },
  available_actions: ["log_manual_execution"],
  blocked_actions: ["modify_deferred", "broker_write_not_available", "automatic_execution_not_available", "approve_already_recorded", "reject_not_available_after_approval"],
};

const approveResponse: TicketActionResponse = {
  ticket_id: 9801,
  new_ticket_status: "approved",
  ticket: approvedTicketDetail.ticket,
  ticket_events: [...mockTicketDetail.ticket_events, { event_id: 2, order_ticket_id: 9801, event_type: "approved", from_status: "validated", to_status: "approved", event_payload: { reason: "테스트 승인" }, created_at: "2026-06-16T08:20:00Z" }],
  linked_decision_journal_entry_id: 77,
  available_actions: ["log_manual_execution"],
  blocked_actions: approvedTicketDetail.blocked_actions,
};

const rejectResponse: TicketActionResponse = {
  ticket_id: 9801,
  new_ticket_status: "rejected",
  ticket: { ...mockTicketDetail.ticket, status: "rejected", human_decision: "rejected", human_decision_reason: "보류", rejected_at: "2026-06-16T08:21:00Z" },
  ticket_events: [...mockTicketDetail.ticket_events, { event_id: 2, order_ticket_id: 9801, event_type: "rejected", from_status: "validated", to_status: "rejected", event_payload: { reason: "보류" }, created_at: "2026-06-16T08:21:00Z" }],
  linked_decision_journal_entry_id: 78,
  available_actions: [],
  blocked_actions: ["modify_deferred", "broker_write_not_available", "automatic_execution_not_available", "ticket_not_actionable", "manual_execution_not_available"],
};

const loggedExecution: ManualExecutionResponse = {
  execution_id: 9901,
  execution_status: "pending_reconciliation",
  created_transaction_id: 9902,
  linked_ticket_id: 9801,
  execution: {
    manual_execution_id: 9901,
    order_ticket_id: 9801,
    override_ticket_id: null,
    created_transaction_id: 9902,
    account_id: 9001,
    instrument_id: 9101,
    side: "buy",
    executed_quantity: "2.000000",
    executed_price: "151.25",
    gross_amount: "302.50",
    fee_amount: "0.25",
    tax_amount: "0",
    net_cash_amount: "-302.75",
    currency: "USD",
    executed_at: "2026-06-16T08:30:00Z",
    broker_execution_ref: "DEMO-REF",
    execution_status: "pending_reconciliation",
    reconciliation_deadline: null,
    reconciled_at: null,
    reconciliation_id: null,
    notes: "기록",
  },
  linked_ticket: approvedTicketDetail.ticket,
  provisional_transaction: {
    transaction_id: 9902,
    account_id: 9001,
    instrument_id: 9101,
    transaction_type: "buy",
    trade_date: "2026-06-16",
    currency: "USD",
    quantity: "2.000000",
    price: "151.25",
    gross_amount: "302.50",
    fee_amount: "0.25",
    tax_amount: "0",
    net_cash_amount: "-302.75",
    source: "manual",
    external_ref: "DEMO-REF",
    is_confirmed: false,
  },
  pending_reconciliation: true,
  transaction_is_confirmed: false,
  reconciliation_evidence: null,
  confirmation_eligible: false,
  confirmation_blocked_reason: "transaction_not_confirmed",
  available_actions: ["await_reconciliation"],
  blocked_actions: ["broker_write_not_available", "automatic_execution_not_available", "transaction_not_confirmed"],
  explanation: "Manual execution was recorded as a provisional transaction and awaits reconciliation.",
};

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

function renderTicketDetail() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/tickets/9801"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function baseFetch(status: "passed" | "adjusted" | "rejected" = "passed") {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/accounts") return json(mockAccounts);
    if (url === "/api/v1/instruments") return json(mockInstruments);
    if (url === "/api/v1/intents" && init?.method === "POST") return json(createdIntent, 201);
    if (url === "/api/v1/intents/321/validate" && init?.method === "POST") return json(validation(status));
    if (url === "/api/v1/tickets" && init?.method === "POST") return json(createdTicket, 201);
    if (url === "/api/v1/tickets/9801/approve" && init?.method === "POST") return json(approveResponse);
    if (url === "/api/v1/tickets/9801/reject" && init?.method === "POST") return json(rejectResponse);
    if (url === "/api/v1/tickets/9801") return json(mockTicketDetail);
    if (url === "/api/v1/executions" && init?.method === "POST") return json(loggedExecution, 201);
    throw new Error(`Unhandled request: ${init?.method ?? "GET"} ${url}`);
  });
}

afterEach(() => cleanup());

describe("RiskWorkspacePage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders the Stage 4 workspace shell", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderWithClient(<RiskWorkspacePage />);
    expect(await screen.findByRole("heading", { name: "리스크 엔진" })).toBeInTheDocument();
    expect(screen.getByText(/자동 주문/)).toBeInTheDocument();
  });
});

describe("TicketDetailPage", () => {
  beforeEach(() => {
    apiRuntime.retryLive();
    vi.restoreAllMocks();
  });

  it("renders linked ticket, risk validation, intent, actions, and event timeline", async () => {
    vi.stubGlobal("fetch", baseFetch());
    renderTicketDetail();
    expect(await screen.findByRole("heading", { name: "티켓 검토 #9801" })).toBeInTheDocument();
    expect(screen.getByText("이 티켓은 자동 주문이 아닙니다.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "티켓 승인" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "티켓 거절" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "티켓 수정 Stage 6" })).toBeDisabled();
    expect(screen.getByText("#RV-9601")).toBeInTheDocument();
    expect(screen.getByText("created")).toBeInTheDocument();
    expect(screen.getAllByText("302.5 USD").length).toBeGreaterThan(0);
    expect(within(screen.getByRole("table", { name: "티켓 이벤트 타임라인" })).getByText("validated")).toBeInTheDocument();
  });

  it("submits approval and rejection decisions through the API", async () => {
    vi.stubGlobal("fetch", baseFetch());
    const user = userEvent.setup();
    renderTicketDetail();
    await user.click(await screen.findByRole("button", { name: "티켓 승인" }));
    await user.type(screen.getByLabelText("승인 메모"), "테스트 승인");
    await user.click(screen.getByRole("button", { name: "승인 기록 저장" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/tickets/9801/approve", expect.objectContaining({ method: "POST" })));

    await user.click(screen.getByRole("button", { name: "티켓 거절" }));
    await user.type(screen.getByLabelText("거절 사유"), "보류");
    await user.click(screen.getByRole("button", { name: "거절 기록 저장" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/tickets/9801/reject", expect.objectContaining({ method: "POST" })));
  });

  it("shows manual execution form only after approved state and logs pending reconciliation", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/v1/tickets/9801") return json(approvedTicketDetail);
      if (url === "/api/v1/executions" && init?.method === "POST") return json(loggedExecution, 201);
      throw new Error(`Unhandled request: ${init?.method ?? "GET"} ${url}`);
    }));
    const user = userEvent.setup();
    renderTicketDetail();
    expect(await screen.findByRole("button", { name: "수동 실행 기록 저장" })).toBeEnabled();
    await user.type(screen.getByLabelText("체결 수량"), "2");
    await user.type(screen.getByLabelText("체결 가격"), "151.25");
    await user.clear(screen.getByLabelText("수수료"));
    await user.type(screen.getByLabelText("수수료"), "0.25");
    await user.type(screen.getByLabelText("실행 시각"), "2026-06-16T08:30");
    await user.type(screen.getByLabelText("브로커 참고번호"), "DEMO-REF");
    await user.click(screen.getByRole("button", { name: "수동 실행 기록 저장" }));
    expect(await screen.findByText("수동 실행 기록 완료")).toBeInTheDocument();
    expect(screen.getByText("#9902")).toBeInTheDocument();
  });

  it("disables Stage 5 mutation controls in mock mode", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderTicketDetail();
    expect(await screen.findByRole("button", { name: "티켓 승인" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "티켓 거절" })).toBeDisabled();
    expect(screen.getByText("MOCK MODE에서는 승인, 거절, 수동 실행 기록을 만들 수 없습니다.")).toBeInTheDocument();
  });
});
