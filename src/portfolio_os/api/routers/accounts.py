from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.schemas.accounts import AccountListResponse, AccountSchema
from portfolio_os.db import Database
from portfolio_os.repositories import AccountRepository

router = APIRouter(tags=["accounts"])


@router.get("/accounts", response_model=AccountListResponse)
async def get_accounts(db: Database = Depends(get_database)) -> AccountListResponse:
    accounts = AccountRepository(db).list_all_accounts()
    active_count = sum(account.is_active for account in accounts)
    return AccountListResponse(
        count=len(accounts),
        active_count=active_count,
        inactive_count=len(accounts) - active_count,
        accounts=[AccountSchema.model_validate(account) for account in accounts],
    )
