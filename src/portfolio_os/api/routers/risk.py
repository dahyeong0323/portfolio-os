from __future__ import annotations

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.risk import RiskValidationDetailResponse, RiskValidationSchema
from portfolio_os.db import Database
from portfolio_os.risk.repositories import RiskValidationRepository

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/validations/{risk_validation_id}", response_model=RiskValidationDetailResponse)
async def get_risk_validation(
    risk_validation_id: int,
    db: Database = Depends(get_database),
) -> RiskValidationDetailResponse:
    try:
        validation = RiskValidationRepository(db).get(risk_validation_id)
    except ValueError as exc:
        raise ApiError(404, "risk_validation_not_found", "The risk validation result was not found.") from exc
    return RiskValidationDetailResponse(
        validation=RiskValidationSchema.model_validate(validation),
        associated_intent_id=validation.intent_id,
        generated_at=validation.created_at,
    )
