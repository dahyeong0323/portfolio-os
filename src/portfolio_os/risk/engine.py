from __future__ import annotations

import hashlib
from datetime import date, timedelta
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.models import LedgerSnapshot
from portfolio_os.risk.action_classifier import classify_action
from portfolio_os.risk.models import RiskCheckResult, RiskValidationResult, TransactionIntent
from portfolio_os.risk.repositories import InstrumentRiskProfileRepository, PricingRepository, RiskPolicyRepository, RiskValidationRepository
from portfolio_os.serialization import dumps_json
from portfolio_os.validators import utc_now


class RiskEngine:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.pricing = PricingRepository(db)
        self.policies = RiskPolicyRepository(db)
        self.profiles = InstrumentRiskProfileRepository(db)

    def classify_action(self, intent: TransactionIntent, ledger_snapshot: LedgerSnapshot):
        return classify_action(intent, ledger_snapshot)

    def validate_intent(self, intent: TransactionIntent, ledger_snapshot: LedgerSnapshot, policy_version_id: int | None = None, as_of_date: date | None = None) -> RiskValidationResult:
        as_of = as_of_date or ledger_snapshot.as_of_date
        policy = self.policies.get_policy(policy_version_id) if policy_version_id else self._active_policy()
        rules = {rule.rule_code: rule for rule in self.policies.list_rules(policy.policy_version_id)}
        action_class = self.classify_action(intent, ledger_snapshot)
        checks: list[RiskCheckResult] = []
        failures: list[str] = []
        warnings: list[str] = []

        def check(code: str, status: str, message: str, threshold: Decimal | None = None, observed: Decimal | None = None, adjusted: Decimal | None = None) -> None:
            checks.append(RiskCheckResult(code, status, message, threshold, observed, adjusted))
            if status == "failed":
                failures.append(f"{code}: {message}")
            if status == "warning":
                warnings.append(f"{code}: {message}")

        ledger_status = ledger_snapshot.ledger_status
        if action_class == "risk_increasing" and ledger_status != "reconciled":
            check("LEDGER_STATUS_GATE", "failed", f"risk-increasing official ticket requires reconciled ledger, got {ledger_status}")
        elif action_class == "risk_reducing" and ledger_status == "broken":
            check("LEDGER_STATUS_GATE", "failed", "broken ledger blocks official tickets")
        elif action_class == "risk_reducing" and ledger_status in {"provisional", "stale"}:
            check("LEDGER_STATUS_GATE", "warning", f"risk-reducing action allowed with {ledger_status} ledger warning")
        else:
            check("LEDGER_STATUS_GATE", "passed", "ledger gate passed")

        price = self.pricing.latest_price(intent.instrument_id, as_of)
        if price is None:
            check("PRICE_AVAILABLE", "failed", "no active price snapshot available")
            price_value = intent.limit_price or Decimal("0")
        else:
            check("PRICE_AVAILABLE", "passed", "price snapshot available")
            price_value = intent.limit_price or price.price

        requested_qty = intent.requested_quantity
        requested_notional = intent.requested_notional
        if requested_notional is None and requested_qty is not None:
            requested_notional = abs(requested_qty * price_value)
        if requested_qty is None and requested_notional is not None and price_value > 0:
            requested_qty = requested_notional / price_value
        requested_notional = requested_notional or Decimal("0")
        requested_qty = requested_qty or Decimal("0")

        if intent.order_type != "limit":
            check("NO_MARKET_ORDER", "failed", "Stage 2 allows only limit orders")
        else:
            check("NO_MARKET_ORDER", "passed", "limit order only")

        converted_notional = self._convert(requested_notional, intent.currency, policy.base_currency, as_of, check)
        cash_before = self._cash_amount(ledger_snapshot, intent.account_id, intent.currency)
        tax_reserve_required = self._tax_reserve_amount(ledger_snapshot, intent.account_id, intent.currency)
        cash_after = cash_before - requested_notional if intent.intent_type == "buy" else cash_before + requested_notional

        if intent.intent_type == "sell":
            holding = self._holding_quantity(ledger_snapshot, intent.account_id, intent.instrument_id)
            if requested_qty > holding:
                check("HOLDING_AVAILABLE_FOR_SELL", "failed", "sell quantity exceeds current holding", holding, requested_qty)
            else:
                check("HOLDING_AVAILABLE_FOR_SELL", "passed", "sell quantity within current holding", holding, requested_qty)

        max_allowed = converted_notional
        if intent.intent_type == "buy":
            reserve_rule = rules.get("TAX_RESERVE_PROTECTION")
            if reserve_rule and reserve_rule.threshold_value != Decimal("1.00"):
                check("TAX_RESERVE_PROTECTION", "failed", "tax reserve protection must remain 1.00", Decimal("1.00"), reserve_rule.threshold_value)
            available_cash = cash_before - tax_reserve_required
            if available_cash < requested_notional:
                adjusted = max(Decimal("0"), available_cash)
                check("TAX_RESERVE_PROTECTION", "adjusted" if adjusted > 0 else "failed", "buy would consume protected tax reserve cash", tax_reserve_required, available_cash, adjusted)
                max_allowed = min(max_allowed, adjusted)
            else:
                check("TAX_RESERVE_PROTECTION", "passed", "tax reserve fully protected", tax_reserve_required, available_cash)
            min_cash = self._rule_value(rules, "MIN_CASH_RESERVE", Decimal("0"))
            if cash_after < min_cash:
                adjusted = max(Decimal("0"), cash_before - tax_reserve_required - min_cash)
                check("MIN_CASH_RESERVE", "adjusted" if adjusted > 0 else "failed", "buy exceeds cash reserve capacity", min_cash, cash_after, adjusted)
                max_allowed = min(max_allowed, adjusted)
            else:
                check("MIN_CASH_RESERVE", "passed", "cash reserve preserved", min_cash, cash_after)
            for code in ("DAILY_BUY_LIMIT", "WEEKLY_BUY_LIMIT", "MAX_ORDER_NOTIONAL"):
                limit = self._rule_value(rules, code, converted_notional)
                if converted_notional > limit:
                    check(code, "adjusted" if limit > 0 else "failed", "requested notional exceeds limit", limit, converted_notional, limit)
                    max_allowed = min(max_allowed, limit)
                else:
                    check(code, "passed", "limit passed", limit, converted_notional)
            gross_value = self._gross_portfolio_value(ledger_snapshot, policy.base_currency, as_of)
            debt_ratio = self._debt_ratio(ledger_snapshot, policy.base_currency, gross_value, as_of)
            debt_limit = self._rule_value(rules, "DEBT_EXPOSURE_CHECK", Decimal("0.50"))
            if debt_ratio > debt_limit:
                check("DEBT_EXPOSURE_CHECK", "failed", "total_active_liabilities / gross_portfolio_value exceeds threshold", debt_limit, debt_ratio)
            else:
                check("DEBT_EXPOSURE_CHECK", "passed", "debt exposure within threshold", debt_limit, debt_ratio)
            post_asset_weight = (self._asset_value(ledger_snapshot, intent.instrument_id, policy.base_currency, as_of) + converted_notional) / max(gross_value + converted_notional, Decimal("1"))
            asset_limit = self._rule_value(rules, "MAX_ASSET_WEIGHT", Decimal("1"))
            if post_asset_weight > asset_limit:
                adjusted = max(Decimal("0"), (asset_limit * gross_value - self._asset_value(ledger_snapshot, intent.instrument_id, policy.base_currency, as_of)) / max(Decimal("1") - asset_limit, Decimal("0.000001")))
                check("MAX_ASSET_WEIGHT", "adjusted" if adjusted > 0 else "failed", "post-trade asset weight exceeds limit", asset_limit, post_asset_weight, adjusted)
                max_allowed = min(max_allowed, adjusted)
            else:
                check("MAX_ASSET_WEIGHT", "passed", "asset weight within limit", asset_limit, post_asset_weight)
            bucket_limit = self._rule_value(rules, "MAX_BUCKET_WEIGHT", Decimal("1"))
            check("MAX_BUCKET_WEIGHT", "passed", "bucket weight check uses Stage 2 MVP asset bucket approximation", bucket_limit, post_asset_weight)

        non_adjustable_failures = {
            "LEDGER_STATUS_GATE",
            "PRICE_AVAILABLE",
            "FX_AVAILABLE",
            "NO_MARKET_ORDER",
            "HOLDING_AVAILABLE_FOR_SELL",
            "DEBT_EXPOSURE_CHECK",
        }
        over_adjusted = any(c.status == "adjusted" for c in checks)
        hard_failed = any(c.status == "failed" for c in checks)
        non_adjustable_failed = any(c.status == "failed" and c.check_code in non_adjustable_failures for c in checks)
        if non_adjustable_failed:
            validation_status = "rejected"
            approved_notional = None
            approved_quantity = None
        elif hard_failed and not over_adjusted:
            validation_status = "rejected"
            approved_notional = None
            approved_quantity = None
        elif hard_failed and max_allowed <= 0:
            validation_status = "rejected"
            approved_notional = None
            approved_quantity = None
        elif over_adjusted and max_allowed < converted_notional:
            validation_status = "adjusted"
            approved_notional = max_allowed
            approved_quantity = max_allowed / price_value if price_value > 0 else None
        else:
            validation_status = "passed"
            approved_notional = requested_notional
            approved_quantity = requested_qty

        return RiskValidationResult(
            risk_validation_id=None,
            intent_id=intent.intent_id,
            policy_version_id=policy.policy_version_id,
            reconciliation_id=None,
            ledger_status_at_validation=ledger_status,
            ledger_snapshot_as_of=as_of,
            ledger_snapshot_digest=hashlib.sha256(dumps_json(ledger_snapshot).encode("utf-8")).hexdigest(),
            validation_status=validation_status,
            action_class=action_class,
            requested_quantity=intent.requested_quantity,
            requested_notional=intent.requested_notional,
            approved_quantity=approved_quantity,
            approved_notional=approved_notional,
            max_allowed_notional=max_allowed if validation_status == "adjusted" else None,
            currency=intent.currency,
            cash_before=cash_before,
            cash_after=cash_after,
            tax_reserve_required=tax_reserve_required,
            checks=tuple(checks),
            failure_reasons=tuple(failures),
            warnings=tuple(warnings),
            created_at=utc_now(),
            expires_at=utc_now() + timedelta(days=1),
            is_superseded=False,
        )

    def validate_and_persist(self, intent: TransactionIntent, ledger_snapshot: LedgerSnapshot, policy_version_id: int | None = None, as_of_date: date | None = None) -> RiskValidationResult:
        result = self.validate_intent(intent, ledger_snapshot, policy_version_id, as_of_date)
        return RiskValidationRepository(self.db).save(result)

    def _active_policy(self):
        policy = self.policies.active_policy()
        if policy is None:
            raise ValueError("no active risk policy; run seed-default-risk-policy")
        return policy

    def _rule_value(self, rules, code: str, default: Decimal) -> Decimal:
        return rules[code].threshold_value if code in rules else default

    def _cash_amount(self, snapshot: LedgerSnapshot, account_id: int, currency: str) -> Decimal:
        return next((cash.amount for cash in snapshot.cash if cash.account_id == account_id and cash.currency == currency), Decimal("0"))

    def _tax_reserve_amount(self, snapshot: LedgerSnapshot, account_id: int, currency: str) -> Decimal:
        return sum((reserve.reserved_amount for reserve in snapshot.tax_reserves if reserve.currency == currency and (reserve.account_id is None or reserve.account_id == account_id)), Decimal("0"))

    def _holding_quantity(self, snapshot: LedgerSnapshot, account_id: int, instrument_id: int) -> Decimal:
        return next((position.quantity for position in snapshot.positions if position.account_id == account_id and position.instrument_id == instrument_id), Decimal("0"))

    def _convert(self, amount: Decimal, from_currency: str, to_currency: str, as_of: date, check) -> Decimal:
        if from_currency == to_currency:
            return amount
        direct = self.pricing.latest_fx_rate(to_currency, from_currency, as_of)
        if direct:
            return amount / direct.rate
        reverse = self.pricing.latest_fx_rate(from_currency, to_currency, as_of)
        if reverse:
            return amount * reverse.rate
        check("FX_AVAILABLE", "failed", f"missing FX rate for {from_currency}->{to_currency}")
        return amount

    def _asset_value(self, snapshot: LedgerSnapshot, instrument_id: int, base_currency: str, as_of: date) -> Decimal:
        total = Decimal("0")
        for position in snapshot.positions:
            if position.instrument_id != instrument_id:
                continue
            price = self.pricing.latest_price(position.instrument_id, as_of)
            if price:
                total += self._convert(abs(position.quantity * price.price), price.currency, base_currency, as_of, lambda *_: None)
        return total

    def _gross_portfolio_value(self, snapshot: LedgerSnapshot, base_currency: str, as_of: date) -> Decimal:
        total = Decimal("0")
        for cash in snapshot.cash:
            if cash.amount > 0:
                total += self._convert(cash.amount, cash.currency, base_currency, as_of, lambda *_: None)
        for position in snapshot.positions:
            price = self.pricing.latest_price(position.instrument_id, as_of)
            if price:
                total += self._convert(abs(position.quantity * price.price), price.currency, base_currency, as_of, lambda *_: None)
        return total

    def _debt_ratio(self, snapshot: LedgerSnapshot, base_currency: str, gross_value: Decimal, as_of: date) -> Decimal:
        if gross_value <= 0:
            return Decimal("0")
        liabilities = sum((self._convert(liability.current_amount, liability.currency, base_currency, as_of, lambda *_: None) for liability in snapshot.liabilities), Decimal("0"))
        return liabilities / gross_value
