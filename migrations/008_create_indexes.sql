CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_institution ON accounts(institution_name);

CREATE INDEX IF NOT EXISTS idx_instruments_type ON instruments(instrument_type);
CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);

CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_transactions_instrument ON transactions(instrument_id);
CREATE INDEX IF NOT EXISTS idx_transactions_confirmed ON transactions(is_confirmed);
CREATE INDEX IF NOT EXISTS idx_transactions_external_ref ON transactions(source, external_ref);
CREATE INDEX IF NOT EXISTS idx_transactions_voided ON transactions(is_voided);

CREATE INDEX IF NOT EXISTS idx_cash_balances_date ON cash_balances(as_of_date);
CREATE INDEX IF NOT EXISTS idx_cash_balances_reconciled ON cash_balances(is_reconciled);

CREATE INDEX IF NOT EXISTS idx_liabilities_active ON liabilities(is_active);
CREATE INDEX IF NOT EXISTS idx_liabilities_as_of ON liabilities(as_of_date);
CREATE INDEX IF NOT EXISTS idx_liabilities_account ON liabilities(account_id);

CREATE INDEX IF NOT EXISTS idx_tax_reserves_year ON tax_reserves(tax_year);
CREATE INDEX IF NOT EXISTS idx_tax_reserves_active ON tax_reserves(is_active);
CREATE INDEX IF NOT EXISTS idx_tax_reserves_account ON tax_reserves(account_id);

CREATE INDEX IF NOT EXISTS idx_recon_account_date ON reconciliation_snapshots(account_id, as_of_date);
CREATE INDEX IF NOT EXISTS idx_recon_status ON reconciliation_snapshots(reconciliation_status);
CREATE INDEX IF NOT EXISTS idx_recon_ledger_after ON reconciliation_snapshots(ledger_status_after);
CREATE INDEX IF NOT EXISTS idx_recon_completed ON reconciliation_snapshots(completed_at);
