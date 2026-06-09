CREATE INDEX IF NOT EXISTS idx_senior_input_bundle_date ON senior_memo_input_bundles(as_of_date);
CREATE INDEX IF NOT EXISTS idx_senior_input_bundle_ledger ON senior_memo_input_bundles(ledger_status);
CREATE INDEX IF NOT EXISTS idx_senior_input_bundle_recon ON senior_memo_input_bundles(latest_reconciliation_id);
CREATE INDEX IF NOT EXISTS idx_senior_input_bundle_portfolio_only ON senior_memo_input_bundles(portfolio_only);

CREATE INDEX IF NOT EXISTS idx_senior_memos_status ON senior_memos(memo_status);
CREATE INDEX IF NOT EXISTS idx_senior_memos_date ON senior_memos(as_of_date);
CREATE INDEX IF NOT EXISTS idx_senior_memos_scope ON senior_memos(memo_scope);
CREATE INDEX IF NOT EXISTS idx_senior_memos_bundle ON senior_memos(input_bundle_id);

CREATE INDEX IF NOT EXISTS idx_senior_sections_memo ON senior_memo_sections(senior_memo_id);
CREATE INDEX IF NOT EXISTS idx_senior_sections_type ON senior_memo_sections(section_type);

CREATE INDEX IF NOT EXISTS idx_decision_candidates_memo ON decision_candidates(senior_memo_id);
CREATE INDEX IF NOT EXISTS idx_decision_candidates_status ON decision_candidates(candidate_status);
CREATE INDEX IF NOT EXISTS idx_decision_candidates_action_class ON decision_candidates(candidate_action_class);

CREATE INDEX IF NOT EXISTS idx_no_action_memo ON no_action_alternatives(senior_memo_id);
CREATE INDEX IF NOT EXISTS idx_opposing_arguments_memo ON opposing_arguments(senior_memo_id);
CREATE INDEX IF NOT EXISTS idx_change_triggers_memo ON decision_change_triggers(senior_memo_id);
CREATE INDEX IF NOT EXISTS idx_senior_qa_memo ON senior_memo_qa_results(senior_memo_id);
