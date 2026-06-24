export type DecimalString = string;
export type LedgerStatus = "reconciled" | "provisional" | "stale" | "broken";
export type ReconciliationStatus = "passed" | "failed" | "needs_review";
export type RiskValidationStatus = "passed" | "adjusted" | "rejected";
export type RiskCheckStatus = "passed" | "failed" | "adjusted" | "warning";
export type TicketStatus =
  | "validated"
  | "approved"
  | "rejected"
  | "modified"
  | "expired"
  | "executed_provisional"
  | "reconciled"
  | "broken"
  | "cancelled";

export interface ErrorEnvelope {
  error: { code: string; message: string; details: unknown };
}

export interface HealthResponse {
  status: "ok" | "degraded";
  api_status: "ok";
  database_reachable: boolean;
  database_ready: boolean;
  app_mode: string;
  migrations: {
    expected_count: number;
    applied_count: number;
    latest_expected_version: number | null;
    latest_applied_version: number | null;
    ready: boolean;
  };
}

export interface LedgerStatusResponse {
  ledger_status: LedgerStatus;
  last_reconciled_at: string | null;
  is_reconciled: boolean;
  is_provisional: boolean;
  is_stale: boolean;
  is_broken: boolean;
  explanation: string;
}

export interface LedgerPosition {
  account_id: number;
  instrument_id: number;
  symbol: string;
  currency: string;
  quantity: DecimalString;
  average_cost: DecimalString | null;
}

export interface LedgerCash {
  account_id: number;
  currency: string;
  amount: DecimalString;
}

export interface ExternalPosition {
  account_id: number;
  symbol: string;
  currency: string;
  quantity: DecimalString;
  exchange: string | null;
  instrument_id: number | null;
  match_status: string;
  match_error: string | null;
}

export interface ExternalLiability {
  account_id: number | null;
  liability_name: string;
  currency: string;
  current_amount: DecimalString;
  liability_type: string | null;
}

export interface ExternalTaxReserve {
  account_id: number | null;
  tax_year: number;
  tax_type: string;
  currency: string;
  reserved_amount: DecimalString;
}

export interface LedgerLiability {
  liability_id: number;
  account_id: number | null;
  liability_name: string;
  liability_type: string;
  currency: string;
  current_amount: DecimalString;
}

export interface LedgerTaxReserve {
  tax_reserve_id: number;
  account_id: number | null;
  tax_year: number;
  tax_type: string;
  currency: string;
  reserved_amount: DecimalString;
}

export interface LedgerSnapshotResponse {
  as_of_date: string;
  positions: LedgerPosition[];
  cash: LedgerCash[];
  liabilities: LedgerLiability[];
  tax_reserves: LedgerTaxReserve[];
  generated_at: string;
  ledger_status: LedgerStatus;
}

export interface Account {
  account_id: number;
  account_name: string;
  institution_name: string;
  account_type: string;
  base_currency: string;
  account_number_masked: string | null;
  is_active: boolean;
  opened_date: string | null;
  closed_date: string | null;
  notes: string | null;
}

export interface AccountListResponse {
  count: number;
  active_count: number;
  inactive_count: number;
  accounts: Account[];
}

export interface Instrument {
  instrument_id: number;
  symbol: string;
  instrument_name: string;
  instrument_type: string;
  exchange: string | null;
  isin: string | null;
  currency: string;
  country: string | null;
  is_fractional_allowed: boolean;
  quantity_precision: number;
  price_precision: number;
  is_active: boolean;
  notes: string | null;
}

export interface InstrumentListResponse {
  count: number;
  active_count: number;
  inactive_count: number;
  instruments: Instrument[];
}

export interface DifferenceBase {
  difference: DecimalString;
  within_tolerance: boolean;
}

export interface PositionDifference extends DifferenceBase {
  account_id: number;
  instrument_id: number | null;
  symbol: string;
  expected_quantity: DecimalString;
  actual_quantity: DecimalString;
}

export interface CashDifference extends DifferenceBase {
  account_id: number;
  currency: string;
  expected_amount: DecimalString;
  actual_amount: DecimalString;
}

export interface LiabilityDifference extends DifferenceBase {
  account_id: number | null;
  liability_name: string;
  currency: string;
  expected_amount: DecimalString;
  actual_amount: DecimalString;
}

export interface TaxReserveDifference extends DifferenceBase {
  account_id: number | null;
  tax_year: number;
  tax_type: string;
  currency: string;
  expected_amount: DecimalString;
  actual_amount: DecimalString;
}

export interface ReconciliationSnapshot {
  reconciliation_id: number;
  account_id: number | null;
  as_of_date: string;
  started_at: string;
  completed_at: string | null;
  ledger_status_before: LedgerStatus;
  ledger_status_after: LedgerStatus;
  reconciliation_status: ReconciliationStatus;
  snapshot_source: string;
  position_diff_count: number;
  cash_diff_count: number;
  liability_diff_count: number;
  tax_reserve_diff_count: number;
  total_abs_cash_diff_base: DecimalString;
  tolerance: { cash_abs: DecimalString; quantity_abs: DecimalString };
  expected_positions: LedgerPosition[];
  actual_positions: ExternalPosition[];
  position_differences: PositionDifference[];
  expected_cash: LedgerCash[];
  actual_cash: LedgerCash[];
  cash_differences: CashDifference[];
  expected_liabilities: LedgerLiability[];
  actual_liabilities: ExternalLiability[];
  liability_differences: LiabilityDifference[];
  expected_tax_reserves: LedgerTaxReserve[];
  actual_tax_reserves: ExternalTaxReserve[];
  tax_reserve_differences: TaxReserveDifference[];
  failure_reason: string | null;
  created_at: string;
}

export interface LatestReconciliationResponse {
  found: boolean;
  reconciliation: ReconciliationSnapshot | null;
}

export interface ExternalSnapshotImportResponse {
  artifact_id: string;
  account_id: number;
  source: string;
  as_of_date: string;
  status: "imported" | "imported_with_warnings";
  counts: {
    positions: number;
    cash: number;
    liabilities: number;
    tax_reserves: number;
  };
  warnings: string[];
  imported_at: string;
}

export interface RunReconciliationRequest {
  artifact_id: string;
  account_id: number;
  as_of_date?: string;
}

export interface RunReconciliationResponse {
  reconciliation_id: number;
  reconciliation_status: ReconciliationStatus;
  ledger_status: LedgerStatus;
  generated_at: string;
  diff_counts: {
    positions: number;
    cash: number;
    liabilities: number;
    tax_reserves: number;
  };
  report_available: boolean;
  report_reference: string | null;
  explanation: string;
  warnings: string[];
}

export interface ReconciliationReportResponse {
  reconciliation_id: number;
  format: "markdown";
  content: string;
  generated_at: string;
  report_reference: string;
}

export type ReportFormat = "markdown" | "json";

export interface ReportCategory {
  category_id: string;
  label: string;
  description: string;
  report_count: number;
  supported_formats: ReportFormat[];
  latest_generated_at: string | null;
}

export interface ReportCategoryListResponse {
  categories: ReportCategory[];
}

export interface ReportListItem {
  report_reference: string;
  category: string;
  title: string;
  format: ReportFormat;
  generated_at: string | null;
  linked_object_type: string | null;
  linked_object_id: string | null;
  safe_summary: string | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface ReportListResponse {
  count: number;
  reports: ReportListItem[];
}

export interface ReportDetailResponse {
  report_reference: string;
  category: string;
  title: string;
  format: ReportFormat;
  content: string;
  generated_at: string | null;
  linked_object_type: string | null;
  linked_object_id: string | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface ResearchItem {
  research_id: number | null;
  report_reference: string | null;
  title: string;
  subject: string | null;
  instrument: string | null;
  thesis: string | null;
  status: string | null;
  created_at: string | null;
  updated_at: string | null;
  linked_report_reference: string | null;
  anti_thesis_present: boolean | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface ResearchListResponse {
  count: number;
  items: ResearchItem[];
}

export interface ResearchDetailResponse {
  metadata: Record<string, unknown>;
  thesis: Record<string, unknown> | null;
  anti_thesis: Record<string, unknown> | null;
  sources: Record<string, unknown>[];
  evidence_summary: Record<string, unknown>;
  linked_reports: string[];
  read_only_explanation: string;
  available_actions: string[];
  blocked_actions: string[];
}

export interface MacroItem {
  macro_id: number | null;
  report_reference: string | null;
  title: string;
  regime: string | null;
  scenario: string | null;
  tags: string[];
  created_at: string | null;
  linked_report_reference: string | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface MacroListResponse {
  count: number;
  items: MacroItem[];
}

export interface MacroDetailResponse {
  metadata: Record<string, unknown>;
  regime: Record<string, unknown> | null;
  scenario: Record<string, unknown>;
  tags: string[];
  linked_reports: string[];
  read_only_explanation: string;
  available_actions: string[];
  blocked_actions: string[];
}

export interface SeniorMemoItem {
  memo_id: number | null;
  report_reference: string | null;
  title: string;
  linked_intent_id: number | null;
  ticket_id: number | null;
  risk_validation_id: number | null;
  recommendation_summary: string | null;
  created_at: string | null;
  linked_report_reference: string | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface SeniorMemoListResponse {
  count: number;
  memos: SeniorMemoItem[];
}

export interface SeniorMemoDetailResponse {
  metadata: Record<string, unknown>;
  input_bundle: Record<string, unknown> | null;
  sections: Record<string, unknown>[];
  decision_candidates: Record<string, unknown>[];
  no_action_alternatives: Record<string, unknown>[];
  opposing_arguments: Record<string, unknown>[];
  linked_reports: string[];
  read_only_explanation: string;
  available_actions: string[];
  blocked_actions: string[];
}

export interface GovernanceOverviewResponse {
  context_package_status: Record<string, unknown> | null;
  canary: Record<string, unknown> | null;
  health: Record<string, unknown> | null;
  stale_context_warnings: string[];
  governance_report_references: string[];
  canary_report_references: string[];
  health_report_references: string[];
  context_report_references: string[];
  available_actions: string[];
  blocked_actions: string[];
}

export interface GovernanceEvent {
  event_id: number;
  event_type: string;
  event_scope: string;
  severity: string;
  related_table: string | null;
  related_id: number | null;
  event_summary: string;
  created_at: string | null;
}

export interface GovernanceEventListResponse {
  count: number;
  events: GovernanceEvent[];
}

export interface OrderTicket {
  order_ticket_id: number;
  intent_id: number;
  risk_validation_id: number;
  account_id: number;
  instrument_id: number;
  side: "buy" | "sell";
  order_type: string;
  ticket_quantity: DecimalString;
  limit_price: DecimalString | null;
  ticket_notional: DecimalString;
  currency: string;
  status: TicketStatus;
  human_decision: string | null;
  human_decision_reason: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  expires_at: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrderTicketListResponse {
  count: number;
  tickets: OrderTicket[];
}

export interface CreateIntentRequest {
  account_id: number;
  instrument_id: number;
  side: "buy" | "sell";
  currency: string;
  requested_quantity?: DecimalString | null;
  requested_notional?: DecimalString | null;
  limit_price?: DecimalString | null;
  rationale?: string | null;
  expires_at?: string | null;
}

export interface TransactionIntent {
  intent_id: number;
  account_id: number;
  instrument_id: number;
  intent_type: "buy" | "sell";
  intent_source: string;
  requested_quantity: DecimalString | null;
  requested_notional: DecimalString | null;
  limit_price: DecimalString | null;
  currency: string;
  order_type: string;
  rationale: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  expires_at: string | null;
}

export interface CreateIntentResponse {
  intent: TransactionIntent;
  next_available_actions: string[];
}

export interface ValidateIntentRequest {
  as_of_date?: string | null;
  policy_version_id?: number | null;
}

export interface RiskCheck {
  check_code: string;
  status: RiskCheckStatus;
  message: string;
  threshold_value: DecimalString | null;
  observed_value: DecimalString | null;
  adjusted_value: DecimalString | null;
}

export interface RiskValidation {
  risk_validation_id: number | null;
  intent_id: number;
  policy_version_id: number;
  reconciliation_id: number | null;
  ledger_status_at_validation: LedgerStatus;
  ledger_snapshot_as_of: string;
  ledger_snapshot_digest: string | null;
  validation_status: RiskValidationStatus;
  action_class: string;
  requested_quantity: DecimalString | null;
  requested_notional: DecimalString | null;
  approved_quantity: DecimalString | null;
  approved_notional: DecimalString | null;
  max_allowed_notional: DecimalString | null;
  currency: string;
  cash_before: DecimalString | null;
  cash_after: DecimalString | null;
  tax_reserve_required: DecimalString | null;
  checks: RiskCheck[];
  failure_reasons: string[];
  warnings: string[];
  created_at: string | null;
  expires_at: string | null;
  is_superseded: boolean;
}

export interface ValidateIntentResponse {
  validation: RiskValidation;
  ledger_status_gate: RiskCheck | null;
  failed_checks: RiskCheck[];
  warnings: string[];
  explanation: string;
  next_available_actions: string[];
}

export interface RiskValidationDetailResponse {
  validation: RiskValidation;
  associated_intent_id: number;
  generated_at: string | null;
}

export interface CreateTicketRequest {
  risk_validation_id: number;
  expires_at?: string | null;
}

export interface CreateTicketResponse {
  ticket: OrderTicket;
  risk_validation_id: number;
  intent_id: number;
  available_actions: string[];
  blocked_actions: string[];
}

export interface TicketDecisionRequest {
  approval_note?: string | null;
  rejection_reason?: string | null;
  emotional_state?: string | null;
}

export interface IntentSummary {
  intent_id: number;
  status: string;
  account_id: number;
  instrument_id: number;
  side: "buy" | "sell";
  requested_quantity: DecimalString | null;
  requested_notional: DecimalString | null;
  limit_price: DecimalString | null;
  currency: string;
  created_at: string | null;
}

export interface OrderTicketEvent {
  event_id: number;
  order_ticket_id: number;
  event_type: string;
  from_status: string | null;
  to_status: string;
  event_payload: Record<string, unknown>;
  created_at: string | null;
}

export interface OrderTicketDetailResponse {
  ticket: OrderTicket;
  linked_risk_validation: RiskValidation;
  linked_intent: IntentSummary;
  ticket_events: OrderTicketEvent[];
  available_actions: string[];
  blocked_actions: string[];
}

export interface TicketActionResponse {
  ticket_id: number;
  new_ticket_status: TicketStatus;
  ticket: OrderTicket;
  ticket_events: OrderTicketEvent[];
  linked_decision_journal_entry_id: number | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface ManualExecution {
  manual_execution_id: number;
  order_ticket_id: number | null;
  override_ticket_id: number | null;
  created_transaction_id: number | null;
  account_id: number;
  instrument_id: number;
  side: "buy" | "sell";
  executed_quantity: DecimalString;
  executed_price: DecimalString;
  gross_amount: DecimalString;
  fee_amount: DecimalString;
  tax_amount: DecimalString;
  net_cash_amount: DecimalString;
  currency: string;
  executed_at: string;
  broker_execution_ref: string | null;
  execution_status: string;
  reconciliation_deadline: string | null;
  reconciled_at: string | null;
  reconciliation_id: number | null;
  notes: string | null;
}

export interface LinkedTicketSummary {
  order_ticket_id: number;
  status: TicketStatus;
  side: "buy" | "sell";
  instrument_id: number;
  ticket_quantity: DecimalString;
  ticket_notional: DecimalString;
  currency: string;
}

export interface PendingExecution extends ManualExecution {
  linked_ticket: LinkedTicketSummary | null;
  pending_reconciliation: boolean;
  transaction_is_confirmed: boolean | null;
  reconciliation_evidence: ReconciliationEvidence | null;
  confirmation_eligible: boolean;
  confirmation_blocked_reason: string | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface ReconciliationEvidence {
  reconciliation_id: number;
  account_id: number | null;
  as_of_date: string;
  reconciliation_status: ReconciliationStatus;
  completed_at: string | null;
}

export interface PendingExecutionListResponse {
  count: number;
  executions: PendingExecution[];
}

export interface LogManualExecutionRequest {
  ticket_id: number;
  filled_quantity: DecimalString;
  fill_price: DecimalString;
  fee: DecimalString;
  tax: DecimalString;
  executed_at: string;
  broker_reference?: string | null;
  notes?: string | null;
}

export interface ProvisionalTransaction {
  transaction_id: number;
  account_id: number;
  instrument_id: number;
  transaction_type: "buy" | "sell";
  trade_date: string;
  currency: string;
  quantity: DecimalString;
  price: DecimalString;
  gross_amount: DecimalString;
  fee_amount: DecimalString;
  tax_amount: DecimalString;
  net_cash_amount: DecimalString;
  source: string;
  external_ref: string | null;
  is_confirmed: boolean;
}

export interface ManualExecutionResponse {
  execution_id: number;
  execution_status: string;
  created_transaction_id: number | null;
  linked_ticket_id: number | null;
  execution: ManualExecution;
  linked_ticket: OrderTicket | null;
  provisional_transaction: ProvisionalTransaction | null;
  pending_reconciliation: boolean;
  transaction_is_confirmed: boolean | null;
  reconciliation_evidence: ReconciliationEvidence | null;
  confirmation_eligible: boolean;
  confirmation_blocked_reason: string | null;
  available_actions: string[];
  blocked_actions: string[];
  explanation: string;
}

export interface ConfirmExecutionsRequest {
  reconciliation_id?: number | null;
  account_id?: number | null;
  as_of_date?: string | null;
  execution_ids?: number[] | null;
}

export interface SkippedExecution {
  execution_id: number | null;
  reason: string;
  detail: string | null;
}

export interface ConfirmExecutionsResponse {
  confirmation_run_id: string;
  reconciliation_id_used: number;
  total_pending_checked: number;
  confirmed_execution_ids: number[];
  still_pending_execution_ids: number[];
  failed_execution_ids: number[];
  skipped_executions: SkippedExecution[];
  explanation: string;
}

export interface DecisionJournalEntry {
  decision_id: number;
  decision_type: string;
  order_ticket_id: number | null;
  override_ticket_id: number | null;
  risk_validation_id: number | null;
  manual_execution_id: number | null;
  human_decision: string;
  reason: string | null;
  emotional_state: string | null;
  context: Record<string, unknown>;
  created_at: string;
}

export interface DecisionJournalListResponse {
  count: number;
  entries: DecisionJournalEntry[];
}

export interface PostmortemTask {
  postmortem_task_id: number;
  order_ticket_id: number | null;
  override_ticket_id: number | null;
  due_date: string;
  status: string;
  prompt_questions: string[];
  completed_decision_id: number | null;
  created_at: string;
  updated_at: string;
  available_actions: string[];
  blocked_actions: string[];
}

export interface PostmortemTaskListResponse {
  count: number;
  tasks: PostmortemTask[];
}

export interface OverrideTicket {
  override_id: number;
  status: string;
  override_type: string;
  account_id: number;
  account_name: string | null;
  instrument_id: number | null;
  instrument_symbol: string | null;
  instrument_name: string | null;
  side: "buy" | "sell" | null;
  requested_quantity: DecimalString | null;
  requested_notional: DecimalString | null;
  currency: string | null;
  human_reason: string;
  human_final_choice: string | null;
  risk_warning: string;
  ledger_status_at_declaration: LedgerStatus;
  mandatory_reconciliation_deadline: string | null;
  mandatory_postmortem_date: string | null;
  created_at: string | null;
  updated_at: string | null;
  linked_postmortem_task_id: number | null;
  available_actions: string[];
  blocked_actions: string[];
}

export interface OverrideListResponse {
  count: number;
  open_count: number;
  overrides: OverrideTicket[];
}

export interface DeclareOverrideRequest {
  override_type: string;
  account_id: number;
  instrument_id?: number | null;
  side?: "buy" | "sell" | null;
  requested_quantity?: DecimalString | null;
  requested_notional?: DecimalString | null;
  currency?: string | null;
  human_reason: string;
  emotional_state?: string | null;
}

export interface OverrideActionRequest {
  emotional_state?: string | null;
}

export interface OverrideResponse {
  override: OverrideTicket;
  linked_journal_entries: DecisionJournalEntry[];
  postmortem_task: PostmortemTask | null;
  explanation: string;
}
