CREATE INDEX IF NOT EXISTS idx_price_snapshots_instrument_date ON price_snapshots(instrument_id, price_date);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_active ON price_snapshots(is_active);

CREATE INDEX IF NOT EXISTS idx_fx_rates_pair_date ON fx_rates(base_currency, quote_currency, rate_date);
CREATE INDEX IF NOT EXISTS idx_fx_rates_active ON fx_rates(is_active);

CREATE INDEX IF NOT EXISTS idx_instrument_risk_profiles_bucket ON instrument_risk_profiles(risk_bucket);
CREATE INDEX IF NOT EXISTS idx_instrument_risk_profiles_active ON instrument_risk_profiles(is_active);

CREATE INDEX IF NOT EXISTS idx_risk_policy_versions_active ON risk_policy_versions(is_active);
CREATE INDEX IF NOT EXISTS idx_risk_rules_policy ON risk_rules(policy_version_id);
CREATE INDEX IF NOT EXISTS idx_risk_rules_code ON risk_rules(rule_code);
CREATE INDEX IF NOT EXISTS idx_risk_rules_active ON risk_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_transaction_intents_account_status ON transaction_intents(account_id, status);
CREATE INDEX IF NOT EXISTS idx_transaction_intents_instrument ON transaction_intents(instrument_id);

CREATE INDEX IF NOT EXISTS idx_risk_validation_intent ON risk_validation_results(intent_id);
CREATE INDEX IF NOT EXISTS idx_risk_validation_status ON risk_validation_results(validation_status);

CREATE INDEX IF NOT EXISTS idx_order_tickets_status ON order_tickets(status);
CREATE INDEX IF NOT EXISTS idx_order_tickets_intent ON order_tickets(intent_id);
CREATE INDEX IF NOT EXISTS idx_order_ticket_events_ticket ON order_ticket_events(order_ticket_id);

CREATE INDEX IF NOT EXISTS idx_manual_execution_status ON manual_execution_logs(execution_status);
CREATE INDEX IF NOT EXISTS idx_manual_execution_transaction ON manual_execution_logs(created_transaction_id);

CREATE INDEX IF NOT EXISTS idx_override_tickets_status ON override_tickets(status);
CREATE INDEX IF NOT EXISTS idx_decision_journal_type ON decision_journal(decision_type);
CREATE INDEX IF NOT EXISTS idx_postmortem_tasks_status ON postmortem_tasks(status);
