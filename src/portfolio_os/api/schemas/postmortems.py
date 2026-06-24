from datetime import date, datetime

from portfolio_os.api.schemas import ApiSchema


class PostmortemTaskSchema(ApiSchema):
    postmortem_task_id: int
    order_ticket_id: int | None
    override_ticket_id: int | None
    due_date: date
    status: str
    prompt_questions: list[str]
    completed_decision_id: int | None
    created_at: datetime
    updated_at: datetime
    available_actions: list[str]
    blocked_actions: list[str]


class PostmortemTaskListResponse(ApiSchema):
    count: int
    tasks: list[PostmortemTaskSchema]
