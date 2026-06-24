from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.schemas.postmortems import PostmortemTaskListResponse, PostmortemTaskSchema
from portfolio_os.db import Database
from portfolio_os.journal import PostmortemTaskRepository
from portfolio_os.serialization import loads_json
from portfolio_os.validators import date_from_text, datetime_from_text

router = APIRouter(prefix="/postmortems", tags=["postmortems"])


def _postmortem_actions(status: str) -> tuple[list[str], list[str]]:
    blocked = ["record_completion_deferred", "audit_export_deferred"]
    if status == "scheduled":
        return ["review_task"], blocked
    return [], blocked + ["task_not_actionable"]


def postmortem_schema(row: dict) -> PostmortemTaskSchema:
    available, blocked = _postmortem_actions(row["status"])
    return PostmortemTaskSchema(
        postmortem_task_id=row["postmortem_task_id"],
        order_ticket_id=row["order_ticket_id"],
        override_ticket_id=row["override_ticket_id"],
        due_date=date_from_text(row["due_date"]),
        status=row["status"],
        prompt_questions=loads_json(row["prompt_questions_json"] or "[]"),
        completed_decision_id=row["completed_decision_id"],
        created_at=datetime_from_text(row["created_at"]),
        updated_at=datetime_from_text(row["updated_at"]),
        available_actions=available,
        blocked_actions=blocked,
    )


@router.get("", response_model=PostmortemTaskListResponse)
async def list_postmortem_tasks(
    status: str | None = None,
    linked_override_id: int | None = None,
    linked_ticket_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Database = Depends(get_database),
) -> PostmortemTaskListResponse:
    rows = PostmortemTaskRepository(db).list_filtered(
        status=status,
        override_ticket_id=linked_override_id,
        order_ticket_id=linked_ticket_id,
        limit=max(1, min(limit, 200)),
        offset=max(0, offset),
    )
    return PostmortemTaskListResponse(count=len(rows), tasks=[postmortem_schema(row) for row in rows])
