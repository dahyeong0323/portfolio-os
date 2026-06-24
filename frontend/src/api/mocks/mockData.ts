import type {
  AccountListResponse,
  DecisionJournalEntry,
  DecisionJournalListResponse,
  HealthResponse,
  InstrumentListResponse,
  LatestReconciliationResponse,
  LedgerSnapshotResponse,
  LedgerStatusResponse,
  ManualExecutionResponse,
  OrderTicketDetailResponse,
  OrderTicketListResponse,
  OverrideListResponse,
  OverrideResponse,
  PendingExecutionListResponse,
  PostmortemTask,
  PostmortemTaskListResponse,
  GovernanceEventListResponse,
  GovernanceOverviewResponse,
  MacroDetailResponse,
  MacroListResponse,
  ReportCategoryListResponse,
  ReportDetailResponse,
  ReportListResponse,
  ResearchDetailResponse,
  ResearchListResponse,
  RiskValidationDetailResponse,
  SeniorMemoDetailResponse,
  SeniorMemoListResponse,
} from "../types";

const now = "2026-06-14T08:30:00Z";

export const mockHealth: HealthResponse = {
  status: "ok",
  api_status: "ok",
  database_reachable: true,
  database_ready: true,
  app_mode: "mock-sample-read-only",
  migrations: { expected_count: 63, applied_count: 63, latest_expected_version: 63, latest_applied_version: 63, ready: true },
};

export const mockLedgerStatus: LedgerStatusResponse = {
  ledger_status: "reconciled",
  last_reconciled_at: "2026-06-14T07:45:00Z",
  is_reconciled: true,
  is_provisional: false,
  is_stale: false,
  is_broken: false,
  explanation: "[샘플] 정산 이후 추가 미확정 입력이 없습니다.",
};

export const mockLedgerSnapshot: LedgerSnapshotResponse = {
  as_of_date: "2026-06-14",
  generated_at: now,
  ledger_status: "reconciled",
  positions: [
    { account_id: 9001, instrument_id: 9101, symbol: "DEMO-ALPHA", currency: "USD", quantity: "18.500000", average_cost: "142.35" },
    { account_id: 9001, instrument_id: 9102, symbol: "DEMO-CORE", currency: "CHF", quantity: "42.000000", average_cost: "87.10" },
    { account_id: 9002, instrument_id: 9103, symbol: "DEMO-CASH", currency: "USD", quantity: "120.000000", average_cost: "10.00" },
    { account_id: 9001, instrument_id: 9104, symbol: "DEMO-GROWTH", currency: "USD", quantity: "7.250000", average_cost: "211.80" },
  ],
  cash: [
    { account_id: 9001, currency: "USD", amount: "24850.75" },
    { account_id: 9002, currency: "CHF", amount: "12500.00" },
  ],
  liabilities: [{ liability_id: 9201, account_id: null, liability_name: "[샘플] 정산 예정", liability_type: "other", currency: "CHF", current_amount: "1800.00" }],
  tax_reserves: [{ tax_reserve_id: 9301, account_id: null, tax_year: 2026, tax_type: "estimated", currency: "CHF", reserved_amount: "4200.00" }],
};

export const mockAccounts: AccountListResponse = {
  count: 2,
  active_count: 2,
  inactive_count: 0,
  accounts: [
    { account_id: 9001, account_name: "[샘플] 글로벌 증권", institution_name: "DEMO BANK A", account_type: "securities", base_currency: "CHF", account_number_masked: "DEMO-****-1", is_active: true, opened_date: "2025-01-01", closed_date: null, notes: "가짜 데이터" },
    { account_id: 9002, account_name: "[샘플] 유동성 계정", institution_name: "DEMO BANK B", account_type: "cash", base_currency: "CHF", account_number_masked: "DEMO-****-2", is_active: true, opened_date: "2025-01-01", closed_date: null, notes: "가짜 데이터" },
  ],
};

export const mockInstruments: InstrumentListResponse = {
  count: 4,
  active_count: 4,
  inactive_count: 0,
  instruments: mockLedgerSnapshot.positions.map((position, index) => ({
    instrument_id: position.instrument_id,
    symbol: position.symbol,
    instrument_name: `[샘플] 전략 자산 ${index + 1}`,
    instrument_type: index === 2 ? "cash_equivalent" : "etf",
    exchange: "DEMO",
    isin: null,
    currency: position.currency,
    country: "XX",
    is_fractional_allowed: true,
    quantity_precision: 6,
    price_precision: 2,
    is_active: true,
    notes: "실제 종목이 아닌 샘플 데이터",
  })),
};

export const mockReconciliation: LatestReconciliationResponse = {
  found: true,
  reconciliation: {
    reconciliation_id: 9901,
    account_id: null,
    as_of_date: "2026-06-14",
    started_at: "2026-06-14T07:44:00Z",
    completed_at: "2026-06-14T07:45:00Z",
    ledger_status_before: "provisional",
    ledger_status_after: "reconciled",
    reconciliation_status: "passed",
    snapshot_source: "manual",
    position_diff_count: 0,
    cash_diff_count: 0,
    liability_diff_count: 0,
    tax_reserve_diff_count: 0,
    total_abs_cash_diff_base: "0.00",
    tolerance: { cash_abs: "1.00", quantity_abs: "0.000001" },
    expected_positions: mockLedgerSnapshot.positions,
    actual_positions: mockLedgerSnapshot.positions.map((item) => ({ account_id: item.account_id, symbol: item.symbol, currency: item.currency, quantity: item.quantity, exchange: "DEMO", instrument_id: item.instrument_id, match_status: "matched", match_error: null })),
    position_differences: [],
    expected_cash: mockLedgerSnapshot.cash,
    actual_cash: mockLedgerSnapshot.cash,
    cash_differences: [],
    expected_liabilities: mockLedgerSnapshot.liabilities,
    actual_liabilities: mockLedgerSnapshot.liabilities.map((item) => ({ account_id: item.account_id, liability_name: item.liability_name, liability_type: item.liability_type, currency: item.currency, current_amount: item.current_amount })),
    liability_differences: [],
    expected_tax_reserves: mockLedgerSnapshot.tax_reserves,
    actual_tax_reserves: mockLedgerSnapshot.tax_reserves.map((item) => ({ account_id: item.account_id, tax_year: item.tax_year, tax_type: item.tax_type, currency: item.currency, reserved_amount: item.reserved_amount })),
    tax_reserve_differences: [],
    failure_reason: null,
    created_at: "2026-06-14T07:45:00Z",
  },
};

export const mockReconciliationReport = {
  reconciliation_id: mockReconciliation.reconciliation?.reconciliation_id ?? 0,
  format: "markdown" as const,
  content: "# [샘플] Reconciliation Report\n\nMock mode에서만 표시되는 샘플 보고서입니다.\n",
  generated_at: "2026-06-14T07:45:00Z",
  report_reference: "mock:reconciliation:report",
};

export const mockReportCategories: ReportCategoryListResponse = {
  categories: [
    { category_id: "reconciliation", label: "정산 리포트", description: "[샘플] 정산 보고서 카탈로그", report_count: 1, supported_formats: ["markdown", "json"], latest_generated_at: "2026-06-14T07:45:00Z" },
    { category_id: "risk_validation", label: "리스크 리포트", description: "[샘플] Risk Engine 검증 보고서", report_count: 1, supported_formats: ["markdown", "json"], latest_generated_at: "2026-06-14T08:00:00Z" },
    { category_id: "order_ticket", label: "주문 티켓 리포트", description: "[샘플] 주문 티켓 감사 보고서", report_count: 1, supported_formats: ["markdown", "json"], latest_generated_at: "2026-06-14T08:02:00Z" },
    { category_id: "senior_memo", label: "시니어 메모", description: "[샘플] 시니어 메모 보고서", report_count: 0, supported_formats: ["markdown", "json"], latest_generated_at: null },
    { category_id: "governance", label: "거버넌스", description: "[샘플] 거버넌스 보고서", report_count: 0, supported_formats: ["markdown", "json"], latest_generated_at: null },
    { category_id: "frontend_stage", label: "개발 리포트", description: "[샘플] 프론트엔드 단계 문서", report_count: 1, supported_formats: ["markdown"], latest_generated_at: "2026-06-14T08:30:00Z" },
  ],
};

export const mockReports: ReportListResponse = {
  count: 4,
  reports: [
    { report_reference: "DEMO-REPORT-RECON-1", category: "reconciliation", title: "[샘플] 정산 리포트 #9901", format: "markdown", generated_at: "2026-06-14T07:45:00Z", linked_object_type: "reconciliation", linked_object_id: "9901", safe_summary: "[샘플] Reconciliation Report", available_actions: ["view", "copy", "download"], blocked_actions: ["broker_write", "automatic_execution", "mutate_ledger"] },
    { report_reference: "DEMO-REPORT-RISK-1", category: "risk_validation", title: "[샘플] 리스크 리포트 #9601", format: "markdown", generated_at: "2026-06-14T08:00:00Z", linked_object_type: "risk_validation", linked_object_id: "9601", safe_summary: "[샘플] Risk Validation Report", available_actions: ["view", "copy", "download"], blocked_actions: ["broker_write", "automatic_execution", "mutate_ledger"] },
    { report_reference: "DEMO-REPORT-TICKET-1", category: "order_ticket", title: "[샘플] 주문 티켓 리포트 #9801", format: "json", generated_at: "2026-06-14T08:02:00Z", linked_object_type: "order_ticket", linked_object_id: "9801", safe_summary: "JSON report artifact", available_actions: ["view", "copy", "download"], blocked_actions: ["broker_write", "automatic_execution", "mutate_ledger"] },
    { report_reference: "DEMO-REPORT-STAGE-8", category: "frontend_stage", title: "[샘플] 개발 리포트 Stage 8", format: "markdown", generated_at: "2026-06-14T08:30:00Z", linked_object_type: "frontend_stage", linked_object_id: "8", safe_summary: "[샘플] Frontend implementation report", available_actions: ["view", "copy", "download"], blocked_actions: ["broker_write", "automatic_execution", "mutate_ledger"] },
  ],
};

export const mockReportDetail: ReportDetailResponse = {
  ...mockReports.reports[0]!,
  content: "# [샘플] Reconciliation Report\n\n이 보고서는 mock fallback에서만 표시되는 DEMO-* 자료입니다.\n\n<img src=x onerror=alert(1)>\n\n주문 권한이 아니며 거래, 승인, 실행을 수행하지 않습니다.\n",
};

export const mockResearchItems: ResearchListResponse = {
  count: 1,
  items: [{
    research_id: 9001,
    report_reference: "DEMO-RESEARCH-9001",
    title: "[샘플] DEMO research context",
    subject: "[샘플] HTML-like text stays inert: <img src=x onerror=alert(1)>",
    instrument: "DEMO-ALPHA - Sample asset",
    thesis: "[샘플] durable quality thesis",
    status: "complete",
    created_at: "2026-06-14T08:10:00Z",
    updated_at: "2026-06-14T08:15:00Z",
    linked_report_reference: "DEMO-REPORT-STAGE-8",
    anti_thesis_present: true,
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

export const mockResearchDetail: ResearchDetailResponse = {
  metadata: { research_packet_id: 9001, packet_status: "complete", summary_text: "[샘플] DEMO research detail", instrument: "DEMO-ALPHA - Sample asset" },
  thesis: { thesis_title: "[샘플] durable quality thesis", conviction: "sample" },
  anti_thesis: { present: true, facts: [{ fact_text: "[샘플] valuation risk is not resolved" }] },
  sources: [{ source_id: 1, title: "[샘플] DEMO source", source_type: "mock", publisher: "DEMO", freshness_status: "sample" }],
  evidence_summary: { fact_count: 2, missing_data_count: 1, qa: { status: "sample" } },
  linked_reports: ["DEMO-REPORT-STAGE-8"],
  read_only_explanation: "Research context is read-only evidence. It is not order authority.",
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

export const mockMacroItems: MacroListResponse = {
  count: 1,
  items: [{
    macro_id: 9101,
    report_reference: "DEMO-MACRO-9101",
    title: "[샘플] DEMO macro context",
    regime: "sample-regime",
    scenario: "[샘플] liquidity mixed, correlations elevated",
    tags: ["DEMO-risk-on-neutral", "DEMO-correlation-watch"],
    created_at: "2026-06-14T08:12:00Z",
    linked_report_reference: "DEMO-REPORT-STAGE-8",
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

export const mockMacroDetail: MacroDetailResponse = {
  metadata: { macro_context_packet_id: 9101, summary_text: "[샘플] DEMO macro context" },
  regime: { regime: "sample-regime", confidence: "demo" },
  scenario: { summary_text: "[샘플] scenario only, not a timing signal", unknowns: ["DEMO-inflation-path"] },
  tags: ["DEMO-risk-on-neutral", "DEMO-correlation-watch"],
  linked_reports: ["DEMO-REPORT-STAGE-8"],
  read_only_explanation: "Macro context is scenario context only. It is not a timing signal or order authority.",
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

export const mockSeniorMemos: SeniorMemoListResponse = {
  count: 1,
  memos: [{
    memo_id: 9201,
    report_reference: "DEMO-MEMO-9201",
    title: "[샘플] DEMO senior memo",
    linked_intent_id: 9701,
    ticket_id: 9801,
    risk_validation_id: 9601,
    recommendation_summary: "[샘플] Context only memo. Official ticket flow remains upstream.",
    created_at: "2026-06-14T08:18:00Z",
    linked_report_reference: "DEMO-REPORT-STAGE-8",
    available_actions: ["view", "open_report"],
    blocked_actions: ["create_order", "approve", "execute", "broker_write"],
  }],
};

export const mockSeniorMemoDetail: SeniorMemoDetailResponse = {
  metadata: { senior_memo_id: 9201, memo_title: "[샘플] DEMO senior memo", executive_summary: "[샘플] advisory context" },
  input_bundle: { order_ticket_ids: [9801], risk_validation_ids: [9601] },
  sections: [{ section_title: "Context", section_body: "[샘플] <script>alert(1)</script> stays inert in the UI." }],
  decision_candidates: [{ candidate_label: "[샘플] monitor only", candidate_summary: "No execution authority." }],
  no_action_alternatives: [{ alternative_summary: "[샘플] wait for next reconciliation" }],
  opposing_arguments: [{ argument_summary: "[샘플] thesis fragility remains" }],
  linked_reports: ["DEMO-REPORT-STAGE-8"],
  read_only_explanation: "Senior Memo is advisory context only. Official order ticket creation and approval remain available only through the Risk Engine path.",
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

export const mockGovernanceOverview: GovernanceOverviewResponse = {
  context_package_status: { package: { context_package_id: 9301, package_status: "sample", budget_status: "ok" }, budget: { remaining_tokens: 12345 } },
  canary: { canary_run_id: 9401, status: "sample_passed", created_at: "2026-06-14T08:25:00Z" },
  health: { health_id: 9501, status: "sample_ok", warning_count: 0, failure_count: 0 },
  stale_context_warnings: ["[샘플] Mock governance data is not official."],
  governance_report_references: ["DEMO-REPORT-STAGE-8"],
  canary_report_references: [],
  health_report_references: [],
  context_report_references: [],
  available_actions: ["view", "open_report"],
  blocked_actions: ["create_order", "approve", "execute", "broker_write"],
};

export const mockGovernanceEvents: GovernanceEventListResponse = {
  count: 1,
  events: [{ event_id: 9601, event_type: "DEMO_CONTEXT_CHECK", event_scope: "sample", severity: "info", related_table: null, related_id: null, event_summary: "[샘플] DEMO governance event", created_at: "2026-06-14T08:25:00Z" }],
};

export const mockTickets: OrderTicketListResponse = {
  count: 2,
  tickets: [
    { order_ticket_id: 9801, intent_id: 9701, risk_validation_id: 9601, account_id: 9001, instrument_id: 9101, side: "buy", order_type: "limit", ticket_quantity: "2.000000", limit_price: "151.25", ticket_notional: "302.50", currency: "USD", status: "validated", human_decision: null, human_decision_reason: null, approved_at: null, rejected_at: null, expires_at: "2026-06-15T08:00:00Z", created_at: "2026-06-14T08:00:00Z", updated_at: "2026-06-14T08:00:00Z" },
    { order_ticket_id: 9802, intent_id: 9702, risk_validation_id: 9602, account_id: 9001, instrument_id: 9104, side: "sell", order_type: "limit", ticket_quantity: "1.000000", limit_price: "225.00", ticket_notional: "225.00", currency: "USD", status: "approved", human_decision: "approved", human_decision_reason: "[샘플] 검토 완료", approved_at: "2026-06-14T08:05:00Z", rejected_at: null, expires_at: "2026-06-15T08:00:00Z", created_at: "2026-06-14T07:58:00Z", updated_at: "2026-06-14T08:05:00Z" },
  ],
};

const mockPrimaryTicket = mockTickets.tickets[0]!;

export const mockRiskValidation: RiskValidationDetailResponse = {
  associated_intent_id: 9701,
  generated_at: "2026-06-14T08:00:00Z",
  validation: {
    risk_validation_id: 9601,
    intent_id: 9701,
    policy_version_id: 1,
    reconciliation_id: null,
    ledger_status_at_validation: "reconciled",
    ledger_snapshot_as_of: "2026-06-14",
    ledger_snapshot_digest: "DEMO-DIGEST",
    validation_status: "passed",
    action_class: "risk_increasing",
    requested_quantity: null,
    requested_notional: "302.50",
    approved_quantity: "2.000000",
    approved_notional: "302.50",
    max_allowed_notional: null,
    currency: "USD",
    cash_before: "24850.75",
    cash_after: "24548.25",
    tax_reserve_required: "0",
    checks: [
      { check_code: "LEDGER_STATUS_GATE", status: "passed", message: "[샘플] ledger gate passed", threshold_value: null, observed_value: null, adjusted_value: null },
      { check_code: "MAX_ORDER_NOTIONAL", status: "passed", message: "[샘플] limit passed", threshold_value: "1000", observed_value: "302.50", adjusted_value: null },
    ],
    failure_reasons: [],
    warnings: [],
    created_at: "2026-06-14T08:00:00Z",
    expires_at: "2026-06-15T08:00:00Z",
    is_superseded: false,
  },
};

export const mockTicketDetail: OrderTicketDetailResponse = {
  ticket: mockPrimaryTicket,
  linked_risk_validation: mockRiskValidation.validation,
  linked_intent: { intent_id: 9701, status: "ticket_created", account_id: 9001, instrument_id: 9101, side: "buy", requested_quantity: null, requested_notional: "302.50", limit_price: "151.25", currency: "USD", created_at: "2026-06-14T07:58:00Z" },
  ticket_events: [{ event_id: 1, order_ticket_id: mockPrimaryTicket.order_ticket_id, event_type: "created", from_status: null, to_status: "validated", event_payload: { risk_validation_id: 9601 }, created_at: "2026-06-14T08:00:00Z" }],
  available_actions: ["approve_ticket", "reject_ticket"],
  blocked_actions: ["modify_deferred", "manual_execution_requires_approval"],
};

export const mockExecutions: PendingExecutionListResponse = {
  count: 1,
  executions: [{
    manual_execution_id: 9501,
    order_ticket_id: 9802,
    override_ticket_id: null,
    created_transaction_id: 9401,
    account_id: 9001,
    instrument_id: 9104,
    side: "sell",
    executed_quantity: "1.000000",
    executed_price: "224.80",
    gross_amount: "224.80",
    fee_amount: "0.20",
    tax_amount: "0.00",
    net_cash_amount: "224.60",
    currency: "USD",
    executed_at: "2026-06-14T08:10:00Z",
    broker_execution_ref: "DEMO-EXEC-001",
    execution_status: "pending_reconciliation",
    reconciliation_deadline: "2026-06-15",
    reconciled_at: null,
    reconciliation_id: null,
    notes: "[샘플] 정산 대기",
    linked_ticket: { order_ticket_id: 9802, status: "executed_provisional", side: "sell", instrument_id: 9104, ticket_quantity: "1.000000", ticket_notional: "225.00", currency: "USD" },
    pending_reconciliation: true,
    transaction_is_confirmed: true,
    reconciliation_evidence: { reconciliation_id: 9901, account_id: null, as_of_date: "2026-06-14", reconciliation_status: "passed", completed_at: "2026-06-14T07:45:00Z" },
    confirmation_eligible: true,
    confirmation_blocked_reason: null,
    available_actions: ["confirm_after_reconciliation"],
    blocked_actions: ["broker_write_not_available", "automatic_execution_not_available", "broker_execution_not_available"],
  }],
};

export const mockExecutionDetail: ManualExecutionResponse = {
  execution_id: mockExecutions.executions[0]!.manual_execution_id,
  execution_status: mockExecutions.executions[0]!.execution_status,
  created_transaction_id: mockExecutions.executions[0]!.created_transaction_id,
  linked_ticket_id: mockExecutions.executions[0]!.order_ticket_id,
  execution: mockExecutions.executions[0]!,
  linked_ticket: mockTickets.tickets[1]!,
  provisional_transaction: { transaction_id: 9401, account_id: 9001, instrument_id: 9104, transaction_type: "sell", trade_date: "2026-06-14", currency: "USD", quantity: "-1.000000", price: "224.80", gross_amount: "224.80", fee_amount: "0.20", tax_amount: "0.00", net_cash_amount: "224.60", source: "manual", external_ref: "DEMO-EXEC-001", is_confirmed: true },
  pending_reconciliation: true,
  transaction_is_confirmed: true,
  reconciliation_evidence: mockExecutions.executions[0]!.reconciliation_evidence,
  confirmation_eligible: true,
  confirmation_blocked_reason: null,
  available_actions: ["confirm_after_reconciliation"],
  blocked_actions: ["broker_write_not_available", "automatic_execution_not_available", "broker_execution_not_available"],
  explanation: "[샘플] 수동 실행 기록은 provisional transaction으로 남고 다음 정산을 기다립니다.",
};

export const mockJournalEntry: DecisionJournalEntry = {
  decision_id: 99001,
  decision_type: "override_declared",
  order_ticket_id: null,
  override_ticket_id: 97001,
  risk_validation_id: null,
  manual_execution_id: null,
  human_decision: "declared",
  reason: "[샘플] 공식 Risk Engine 경로 밖의 예외를 기록합니다.",
  emotional_state: "calm",
  context: { report_references: ["DEMO-REPORT-RISK-1"] },
  created_at: "2026-06-14T08:20:00Z",
};

export const mockPostmortemTask: PostmortemTask = {
  postmortem_task_id: 96001,
  order_ticket_id: null,
  override_ticket_id: 97001,
  due_date: "2026-06-21",
  status: "scheduled",
  prompt_questions: ["무엇을 예상했나?", "실제로 무엇이 일어났나?", "다음에는 무엇을 바꿀 것인가?"],
  completed_decision_id: null,
  created_at: "2026-06-14T08:20:00Z",
  updated_at: "2026-06-14T08:20:00Z",
  available_actions: ["review_task"],
  blocked_actions: ["record_completion_deferred", "audit_export_deferred"],
};

export const mockOverrides: OverrideListResponse = {
  count: 1,
  open_count: 1,
  overrides: [{
    override_id: 97001,
    status: "risk_warned",
    override_type: "panic",
    account_id: 9001,
    account_name: "[샘플] Mission Control Account",
    instrument_id: 9104,
    instrument_symbol: "DEMO-ALPHA",
    instrument_name: "[샘플] Alpha Instrument",
    side: "sell",
    requested_quantity: "1.000000",
    requested_notional: null,
    currency: "USD",
    human_reason: "[샘플] 예외 선언 감사 기록",
    human_final_choice: null,
    risk_warning: "[샘플] Override is not an official risk-validated ticket.",
    ledger_status_at_declaration: "reconciled",
    mandatory_reconciliation_deadline: "2026-06-15",
    mandatory_postmortem_date: "2026-06-21",
    created_at: "2026-06-14T08:20:00Z",
    updated_at: "2026-06-14T08:20:00Z",
    linked_postmortem_task_id: mockPostmortemTask.postmortem_task_id,
    available_actions: ["confirm_override", "cancel_override"],
    blocked_actions: ["override_execution_deferred", "broker_write_not_available", "automatic_execution_not_available"],
  }],
};

export const mockOverrideDetail: OverrideResponse = {
  override: mockOverrides.overrides[0]!,
  linked_journal_entries: [mockJournalEntry],
  postmortem_task: mockPostmortemTask,
  explanation: "[샘플] Override는 추천이 아니라 예외 선언 감사 기록입니다.",
};

export const mockJournal: DecisionJournalListResponse = { count: 1, entries: [mockJournalEntry] };
export const mockPostmortems: PostmortemTaskListResponse = { count: 1, tasks: [mockPostmortemTask] };
