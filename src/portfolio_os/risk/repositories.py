from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import (
    FxRate,
    InstrumentRiskProfile,
    PriceSnapshot,
    RiskPolicyVersion,
    RiskRule,
    RiskValidationResult,
)
from portfolio_os.serialization import dumps_json, loads_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, decimal_from_text, decimal_to_text, validate_currency_code


def _bool(value: Any) -> bool:
    return bool(int(value))


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def price_from_row(row: dict[str, Any]) -> PriceSnapshot:
    return PriceSnapshot(row["price_snapshot_id"], row["instrument_id"], date_from_text(row["price_date"]), _dt(row["price_timestamp"]), row["currency"], decimal_from_text(row["price"]), row["source"], row["source_ref"], _bool(row["is_active"]), row["notes"])


def fx_from_row(row: dict[str, Any]) -> FxRate:
    return FxRate(row["fx_rate_id"], date_from_text(row["rate_date"]), row["base_currency"], row["quote_currency"], decimal_from_text(row["rate"]), row["source"], row["source_ref"], _bool(row["is_active"]))


def profile_from_row(row: dict[str, Any]) -> InstrumentRiskProfile:
    return InstrumentRiskProfile(
        row["risk_profile_id"],
        row["instrument_id"],
        row["risk_bucket"],
        _bool(row["is_leveraged"]),
        _bool(row["is_crypto_related"]),
        _bool(row["is_single_name_equity"]),
        decimal_from_text(row["max_asset_weight_override"], allow_none=True),
        decimal_from_text(row["max_order_notional_override"], allow_none=True),
        _bool(row["is_active"]),
        row["notes"],
    )


def policy_from_row(row: dict[str, Any]) -> RiskPolicyVersion:
    return RiskPolicyVersion(row["policy_version_id"], row["policy_name"], row["version"], row["base_currency"], _bool(row["is_active"]), row["description"])


def rule_from_row(row: dict[str, Any]) -> RiskRule:
    return RiskRule(
        risk_rule_id=row["risk_rule_id"],
        policy_version_id=row["policy_version_id"],
        rule_code=row["rule_code"],
        rule_scope=row["rule_scope"],
        threshold_value=decimal_from_text(row["threshold_value"]),
        threshold_unit=row["threshold_unit"],
        severity=row["severity"],
        currency=row["currency"],
        account_id=row["account_id"],
        instrument_id=row["instrument_id"],
        risk_bucket=row["risk_bucket"],
        is_active=_bool(row["is_active"]),
        description=row["description"],
    )


class PricingRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_price(self, instrument_id: int, price_date: date, currency: str, price: Decimal, source: str = "manual", source_ref: str | None = None, notes: str | None = None) -> PriceSnapshot:
        validate_currency_code(currency)
        cursor = self.db.execute(
            "INSERT INTO price_snapshots(instrument_id, price_date, currency, price, source, source_ref, is_active, notes) VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (instrument_id, date_to_text(price_date), currency, decimal_to_text(price, "price"), source, source_ref, notes),
        )
        self.db.commit()
        return self.get_price(cursor.lastrowid)

    def get_price(self, price_snapshot_id: int) -> PriceSnapshot:
        row = self.db.fetch_one("SELECT * FROM price_snapshots WHERE price_snapshot_id = ?", (price_snapshot_id,))
        if row is None:
            raise ValueError(f"price not found: {price_snapshot_id}")
        return price_from_row(row)

    def latest_price(self, instrument_id: int, as_of_date: date) -> PriceSnapshot | None:
        row = self.db.fetch_one(
            "SELECT * FROM price_snapshots WHERE instrument_id = ? AND price_date <= ? AND is_active = 1 ORDER BY price_date DESC, price_snapshot_id DESC LIMIT 1",
            (instrument_id, date_to_text(as_of_date)),
        )
        return price_from_row(row) if row else None

    def record_fx_rate(self, rate_date: date, base_currency: str, quote_currency: str, rate: Decimal, source: str = "manual", source_ref: str | None = None) -> FxRate:
        validate_currency_code(base_currency)
        validate_currency_code(quote_currency)
        cursor = self.db.execute(
            "INSERT INTO fx_rates(rate_date, base_currency, quote_currency, rate, source, source_ref, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (date_to_text(rate_date), base_currency, quote_currency, decimal_to_text(rate, "rate"), source, source_ref),
        )
        self.db.commit()
        return self.get_fx_rate(cursor.lastrowid)

    def get_fx_rate(self, fx_rate_id: int) -> FxRate:
        row = self.db.fetch_one("SELECT * FROM fx_rates WHERE fx_rate_id = ?", (fx_rate_id,))
        if row is None:
            raise ValueError(f"fx rate not found: {fx_rate_id}")
        return fx_from_row(row)

    def latest_fx_rate(self, base_currency: str, quote_currency: str, as_of_date: date) -> FxRate | None:
        if base_currency == quote_currency:
            return FxRate(0, as_of_date, base_currency, quote_currency, Decimal("1"), "system_correction", None, True)
        row = self.db.fetch_one(
            "SELECT * FROM fx_rates WHERE base_currency = ? AND quote_currency = ? AND rate_date <= ? AND is_active = 1 ORDER BY rate_date DESC, fx_rate_id DESC LIMIT 1",
            (base_currency, quote_currency, date_to_text(as_of_date)),
        )
        return fx_from_row(row) if row else None


class RiskPolicyRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_policy(self, policy_name: str, version: str, base_currency: str, is_active: bool = False, description: str | None = None) -> RiskPolicyVersion:
        validate_currency_code(base_currency)
        if is_active:
            self.db.execute("UPDATE risk_policy_versions SET is_active = 0 WHERE is_active = 1")
        cursor = self.db.execute(
            "INSERT INTO risk_policy_versions(policy_name, version, base_currency, is_active, description) VALUES (?, ?, ?, ?, ?)",
            (policy_name, version, base_currency, int(is_active), description),
        )
        self.db.commit()
        return self.get_policy(cursor.lastrowid)

    def get_policy(self, policy_version_id: int) -> RiskPolicyVersion:
        row = self.db.fetch_one("SELECT * FROM risk_policy_versions WHERE policy_version_id = ?", (policy_version_id,))
        if row is None:
            raise ValueError(f"policy not found: {policy_version_id}")
        return policy_from_row(row)

    def active_policy(self) -> RiskPolicyVersion | None:
        row = self.db.fetch_one("SELECT * FROM risk_policy_versions WHERE is_active = 1 LIMIT 1")
        return policy_from_row(row) if row else None

    def add_rule(self, rule: RiskRule) -> RiskRule:
        cursor = self.db.execute(
            """
            INSERT INTO risk_rules(policy_version_id, rule_code, rule_scope, account_id, instrument_id, risk_bucket,
            threshold_value, threshold_unit, currency, severity, is_active, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule.policy_version_id,
                rule.rule_code,
                rule.rule_scope,
                rule.account_id,
                rule.instrument_id,
                rule.risk_bucket,
                decimal_to_text(rule.threshold_value, "threshold_value"),
                rule.threshold_unit,
                rule.currency,
                rule.severity,
                int(rule.is_active),
                rule.description,
            ),
        )
        self.db.commit()
        return self.get_rule(cursor.lastrowid)

    def get_rule(self, risk_rule_id: int) -> RiskRule:
        row = self.db.fetch_one("SELECT * FROM risk_rules WHERE risk_rule_id = ?", (risk_rule_id,))
        if row is None:
            raise ValueError(f"risk rule not found: {risk_rule_id}")
        return rule_from_row(row)

    def list_rules(self, policy_version_id: int) -> list[RiskRule]:
        return [rule_from_row(row) for row in self.db.fetch_all("SELECT * FROM risk_rules WHERE policy_version_id = ? AND is_active = 1", (policy_version_id,))]


class InstrumentRiskProfileRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def set_profile(self, instrument_id: int, risk_bucket: str = "other", is_leveraged: bool = False, is_crypto_related: bool = False, is_single_name_equity: bool = False, max_asset_weight_override: Decimal | None = None, max_order_notional_override: Decimal | None = None, notes: str | None = None) -> InstrumentRiskProfile:
        existing = self.get_profile(instrument_id)
        params = (
            instrument_id,
            risk_bucket,
            int(is_leveraged),
            int(is_crypto_related),
            int(is_single_name_equity),
            decimal_to_text(max_asset_weight_override, allow_none=True),
            decimal_to_text(max_order_notional_override, allow_none=True),
            1,
            notes,
        )
        if existing:
            self.db.execute(
                """
                UPDATE instrument_risk_profiles SET risk_bucket=?, is_leveraged=?, is_crypto_related=?, is_single_name_equity=?,
                max_asset_weight_override=?, max_order_notional_override=?, is_active=?, notes=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now')
                WHERE instrument_id=?
                """,
                (risk_bucket, int(is_leveraged), int(is_crypto_related), int(is_single_name_equity), decimal_to_text(max_asset_weight_override, allow_none=True), decimal_to_text(max_order_notional_override, allow_none=True), 1, notes, instrument_id),
            )
            self.db.commit()
            return self.get_profile(instrument_id)
        cursor = self.db.execute(
            """
            INSERT INTO instrument_risk_profiles(instrument_id, risk_bucket, is_leveraged, is_crypto_related, is_single_name_equity,
            max_asset_weight_override, max_order_notional_override, is_active, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            params,
        )
        self.db.commit()
        row = self.db.fetch_one("SELECT * FROM instrument_risk_profiles WHERE risk_profile_id = ?", (cursor.lastrowid,))
        assert row is not None
        return profile_from_row(row)

    def get_profile(self, instrument_id: int) -> InstrumentRiskProfile | None:
        row = self.db.fetch_one("SELECT * FROM instrument_risk_profiles WHERE instrument_id = ?", (instrument_id,))
        return profile_from_row(row) if row else None


class RiskValidationRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, result: RiskValidationResult) -> RiskValidationResult:
        cursor = self.db.execute(
            """
            INSERT INTO risk_validation_results(intent_id, policy_version_id, reconciliation_id, ledger_status_at_validation,
            ledger_snapshot_as_of, ledger_snapshot_digest, validation_status, action_class, requested_quantity, requested_notional,
            approved_quantity, approved_notional, max_allowed_notional, currency, cash_before, cash_after, tax_reserve_required,
            checks_json, failure_reasons_json, warnings_json, expires_at, is_superseded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.intent_id,
                result.policy_version_id,
                result.reconciliation_id,
                result.ledger_status_at_validation,
                date_to_text(result.ledger_snapshot_as_of),
                result.ledger_snapshot_digest,
                result.validation_status,
                result.action_class,
                decimal_to_text(result.requested_quantity, allow_none=True),
                decimal_to_text(result.requested_notional, allow_none=True),
                decimal_to_text(result.approved_quantity, allow_none=True),
                decimal_to_text(result.approved_notional, allow_none=True),
                decimal_to_text(result.max_allowed_notional, allow_none=True),
                result.currency,
                decimal_to_text(result.cash_before, allow_none=True),
                decimal_to_text(result.cash_after, allow_none=True),
                decimal_to_text(result.tax_reserve_required, allow_none=True),
                dumps_json(result.checks),
                dumps_json(result.failure_reasons),
                dumps_json(result.warnings),
                result.expires_at.isoformat().replace("+00:00", "Z") if result.expires_at else None,
                int(result.is_superseded),
            ),
        )
        self.db.commit()
        return replace(result, risk_validation_id=cursor.lastrowid)

    def get(self, risk_validation_id: int) -> RiskValidationResult:
        row = self.db.fetch_one("SELECT * FROM risk_validation_results WHERE risk_validation_id = ?", (risk_validation_id,))
        if row is None:
            raise ValueError(f"risk validation not found: {risk_validation_id}")
        # Checks are not reconstructed in detail here; services use persisted scalar fields.
        from portfolio_os.risk.models import RiskCheckResult

        checks = tuple(RiskCheckResult(**item) for item in loads_json(row["checks_json"]))
        return RiskValidationResult(
            risk_validation_id=row["risk_validation_id"],
            intent_id=row["intent_id"],
            policy_version_id=row["policy_version_id"],
            reconciliation_id=row["reconciliation_id"],
            ledger_status_at_validation=row["ledger_status_at_validation"],
            ledger_snapshot_as_of=date_from_text(row["ledger_snapshot_as_of"]),
            ledger_snapshot_digest=row["ledger_snapshot_digest"],
            validation_status=row["validation_status"],
            action_class=row["action_class"],
            requested_quantity=decimal_from_text(row["requested_quantity"], allow_none=True),
            requested_notional=decimal_from_text(row["requested_notional"], allow_none=True),
            approved_quantity=decimal_from_text(row["approved_quantity"], allow_none=True),
            approved_notional=decimal_from_text(row["approved_notional"], allow_none=True),
            max_allowed_notional=decimal_from_text(row["max_allowed_notional"], allow_none=True),
            currency=row["currency"],
            cash_before=decimal_from_text(row["cash_before"], allow_none=True),
            cash_after=decimal_from_text(row["cash_after"], allow_none=True),
            tax_reserve_required=decimal_from_text(row["tax_reserve_required"], allow_none=True),
            checks=checks,
            failure_reasons=tuple(loads_json(row["failure_reasons_json"])),
            warnings=tuple(loads_json(row["warnings_json"])),
            created_at=_dt(row["created_at"]),
            expires_at=_dt(row["expires_at"]),
            is_superseded=_bool(row["is_superseded"]),
        )
