from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.intents import CreateIntentRequest, CreateIntentResponse, IntentSchema, ValidateIntentRequest
from portfolio_os.api.schemas.risk import RiskCheckSchema, RiskValidationSchema, ValidateIntentResponse
from portfolio_os.db import Database
from portfolio_os.intents import TransactionIntentRepository, TransactionIntentService
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.repositories import AccountRepository, InstrumentRepository
from portfolio_os.risk import RiskEngine
from portfolio_os.validators import utc_now

router = APIRouter(prefix="/intents", tags=["intents"])


def _intent_actions(status: str) -> list[str]:
    if status in {"drafted", "submitted"}:
        return ["validate_risk"]
    if status in {"risk_passed", "risk_adjusted"}:
        return ["create_ticket"]
    return []


def _validation_explanation(status: str) -> str:
    return {
        "passed": "Risk Engine validation passed. An official manual order ticket may be created.",
        "adjusted": "Risk Engine adjusted the allowed size. A ticket may be created only with the adjusted amount.",
        "rejected": "Risk Engine rejected the intent. An official manual order ticket cannot be created.",
    }[status]


def _validation_actions(status: str) -> list[str]:
    return ["create_ticket"] if status in {"passed", "adjusted"} else []


def _parse_as_of(value: str | None) -> date:
    if value is None:
        return utc_now().date()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ApiError(422, "invalid_as_of_date", "as_of_date must be an ISO date.") from exc


@router.post("", response_model=CreateIntentResponse, status_code=201)
async def create_intent(payload: CreateIntentRequest, db: Database = Depends(get_writable_database)) -> CreateIntentResponse:
    if AccountRepository(db).get_account(payload.account_id) is None:
        raise ApiError(404, "account_not_found", "The selected account was not found.")
    if InstrumentRepository(db).get_instrument(payload.instrument_id) is None:
        raise ApiError(404, "instrument_not_found", "The selected instrument was not found.")
    try:
        intent = TransactionIntentService(db).create_intent(
            payload.account_id,
            payload.instrument_id,
            payload.side,
            payload.currency.upper(),
            payload.requested_quantity,
            payload.requested_notional,
            payload.limit_price,
            payload.rationale,
            payload.expires_at,
        )
    except ValueError as exc:
        raise ApiError(422, "intent_create_failed", "The transaction intent could not be created.", str(exc)) from exc
    return CreateIntentResponse(
        intent=IntentSchema.model_validate(intent),
        next_available_actions=_intent_actions(intent.status),
    )


@router.post("/{intent_id}/validate", response_model=ValidateIntentResponse)
async def validate_intent(
    intent_id: int,
    payload: ValidateIntentRequest,
    db: Database = Depends(get_writable_database),
) -> ValidateIntentResponse:
    intent_repo = TransactionIntentRepository(db)
    try:
        intent = intent_repo.get(intent_id)
    except ValueError as exc:
        raise ApiError(404, "intent_not_found", "The transaction intent was not found.") from exc
    as_of = _parse_as_of(payload.as_of_date)
    try:
        ledger = LedgerSnapshotBuilder(db).build_snapshot(as_of, intent.account_id)
        validation = RiskEngine(db).validate_and_persist(intent, ledger, payload.policy_version_id, as_of)
        intent_repo.update_status(
            intent.intent_id,
            {"passed": "risk_passed", "adjusted": "risk_adjusted", "rejected": "risk_rejected"}[validation.validation_status],
        )
    except ValueError as exc:
        raise ApiError(422, "risk_validation_failed", "The Risk Engine could not validate this intent.", str(exc)) from exc
    checks = [RiskCheckSchema.model_validate(check) for check in validation.checks]
    return ValidateIntentResponse(
        validation=RiskValidationSchema.model_validate(validation),
        ledger_status_gate=next((check for check in checks if check.check_code == "LEDGER_STATUS_GATE"), None),
        failed_checks=[check for check in checks if check.status == "failed"],
        warnings=list(validation.warnings),
        explanation=_validation_explanation(validation.validation_status),
        next_available_actions=_validation_actions(validation.validation_status),
    )
