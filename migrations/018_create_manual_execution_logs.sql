CREATE TABLE IF NOT EXISTS manual_execution_logs (
    manual_execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_ticket_id INTEGER REFERENCES order_tickets(order_ticket_id),
    override_ticket_id INTEGER REFERENCES override_tickets(override_ticket_id),
    created_transaction_id INTEGER REFERENCES transactions(transaction_id),
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    side TEXT NOT NULL CHECK(side IN ('buy','sell')),
    executed_quantity DECIMAL_TEXT NOT NULL CHECK(typeof(executed_quantity) = 'text'),
    executed_price DECIMAL_TEXT NOT NULL CHECK(typeof(executed_price) = 'text'),
    gross_amount DECIMAL_TEXT NOT NULL CHECK(typeof(gross_amount) = 'text'),
    fee_amount DECIMAL_TEXT NOT NULL CHECK(typeof(fee_amount) = 'text'),
    tax_amount DECIMAL_TEXT NOT NULL CHECK(typeof(tax_amount) = 'text'),
    net_cash_amount DECIMAL_TEXT NOT NULL CHECK(typeof(net_cash_amount) = 'text'),
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    executed_at TEXT NOT NULL,
    broker_execution_ref TEXT,
    execution_status TEXT NOT NULL CHECK(execution_status IN ('logged','transaction_created','pending_reconciliation','reconciled','reconciliation_failed','voided')),
    reconciliation_deadline TEXT,
    reconciled_at TEXT,
    reconciliation_id INTEGER REFERENCES reconciliation_snapshots(reconciliation_id),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (
        (order_ticket_id IS NOT NULL AND override_ticket_id IS NULL)
        OR
        (order_ticket_id IS NULL AND override_ticket_id IS NOT NULL)
    )
);
