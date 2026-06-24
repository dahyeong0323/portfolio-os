from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.schemas.instruments import InstrumentListResponse, InstrumentSchema
from portfolio_os.db import Database
from portfolio_os.repositories import InstrumentRepository

router = APIRouter(tags=["instruments"])


@router.get("/instruments", response_model=InstrumentListResponse)
async def get_instruments(db: Database = Depends(get_database)) -> InstrumentListResponse:
    instruments = InstrumentRepository(db).list_all_instruments()
    active_count = sum(instrument.is_active for instrument in instruments)
    return InstrumentListResponse(
        count=len(instruments),
        active_count=active_count,
        inactive_count=len(instruments) - active_count,
        instruments=[InstrumentSchema.model_validate(instrument) for instrument in instruments],
    )
