CREATE TABLE IF NOT EXISTS instrument_risk_profiles (
    risk_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    risk_bucket TEXT NOT NULL CHECK(risk_bucket IN ('core_equity','leveraged_etf','crypto','high_growth','cash_equivalent','other')),
    is_leveraged INTEGER NOT NULL DEFAULT 0 CHECK(is_leveraged IN (0,1)),
    is_crypto_related INTEGER NOT NULL DEFAULT 0 CHECK(is_crypto_related IN (0,1)),
    is_single_name_equity INTEGER NOT NULL DEFAULT 0 CHECK(is_single_name_equity IN (0,1)),
    max_asset_weight_override DECIMAL_TEXT CHECK(max_asset_weight_override IS NULL OR typeof(max_asset_weight_override) = 'text'),
    max_order_notional_override DECIMAL_TEXT CHECK(max_order_notional_override IS NULL OR typeof(max_order_notional_override) = 'text'),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(instrument_id)
);
