CREATE TABLE IF NOT EXISTS transaction_intents (
    intent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    intent_type TEXT NOT NULL CHECK(intent_type IN ('buy','sell')),
    intent_source TEXT NOT NULL CHECK(intent_source IN ('manual','correction','override_precheck')),
    requested_quantity DECIMAL_TEXT CHECK(requested_quantity IS NULL OR typeof(requested_quantity) = 'text'),
    requested_notional DECIMAL_TEXT CHECK(requested_notional IS NULL OR typeof(requested_notional) = 'text'),
    limit_price DECIMAL_TEXT CHECK(limit_price IS NULL OR typeof(limit_price) = 'text'),
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    order_type TEXT NOT NULL CHECK(order_type = 'limit'),
    rationale TEXT,
    status TEXT NOT NULL CHECK(status IN ('drafted','submitted','risk_passed','risk_adjusted','risk_rejected','ticket_created','cancelled','superseded')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    expires_at TEXT,
    CHECK(requested_quantity IS NOT NULL OR requested_notional IS NOT NULL)
);
