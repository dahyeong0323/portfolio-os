from fastapi import APIRouter

from portfolio_os.api.routers import accounts, context_explorer, executions, health, instruments, intents, journal, ledger, overrides, postmortems, reconciliation, reports, risk, snapshots, tickets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ledger.router)
api_router.include_router(accounts.router)
api_router.include_router(instruments.router)
api_router.include_router(intents.router)
api_router.include_router(snapshots.router)
api_router.include_router(reconciliation.router)
api_router.include_router(reports.router)
api_router.include_router(context_explorer.router)
api_router.include_router(risk.router)
api_router.include_router(tickets.router)
api_router.include_router(executions.router)
api_router.include_router(overrides.router)
api_router.include_router(journal.router)
api_router.include_router(postmortems.router)

__all__ = ["api_router"]
