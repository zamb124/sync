"""Роутеры для работы с тредами (Thread)."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.db.repositories.threads import ThreadRepository
from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.models.threads import ThreadCreate, ThreadRead, ThreadSummary
from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.models.users import UserBrief
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.tasks import handle_command
from core.auth.context import require_user
from core.config import settings


router = APIRouter()


@router.get("/", response_model=PaginationResponse[ThreadSummary])
async def list_threads(
    pagination: PaginationRequest = Depends(),
    repo: ThreadRepository = Depends(ThreadRepository),
    messages: MessageRepository = Depends(MessageRepository),
) -> PaginationResponse[ThreadSummary]:
    """Список тредов."""
    rows = await repo.list(limit=pagination.limit, offset=0)
    items: list[ThreadSummary] = []
    for row in rows:
        thread_msgs = await messages.list_by_thread(row.id, limit=500, offset=0)
        replies_count = max(0, len(thread_msgs) - 1)
        last_reply_at = thread_msgs[-1].sent_at if thread_msgs else None
        preview = ""
        if thread_msgs:
            contents = await messages.list_contents(thread_msgs[0].id)
            for c in contents:
                if c.type == "text/plain":
                    body = c.data.get("body")
                    if isinstance(body, str):
                        preview = body[:200]
                        break
        items.append(
            ThreadSummary(
                id=row.id,
                channel_id=row.channel_id,
                root_message_preview=preview,
                replies_count=replies_count,
                last_reply_at=last_reply_at,
            )
        )
    return PaginationResponse[ThreadSummary](items=items, next_cursor=None, prev_cursor=None)


@router.post("/", response_model=ThreadRead)
async def create_thread(payload: ThreadCreate) -> ThreadRead:
    """Создание треда."""
    user_id = require_user().id
    task = await handle_command.kiq(
        CommandEnvelope(
            id=uuid4().hex,
            actor_user_id=user_id,
            type="threads.create",
            payload={"body": payload.model_dump()},
        ).model_dump()
    )
    res = await task.wait_result(timeout=settings.tasks.default_task_timeout)
    if res.is_err:
        raise RuntimeError(str(res.error))
    if not res.return_value.get("ok"):
        raise HTTPException(status_code=422, detail=res.return_value.get("error_detail") or "Ошибка команды.")
    result = res.return_value.get("result")
    if result is None:
        raise RuntimeError("Команда вернула пустой результат.")
    return ThreadRead.model_validate(result)


@router.get("/{thread_id}", response_model=ThreadRead)
async def get_thread(
    thread_id: str,
    repo: ThreadRepository = Depends(ThreadRepository),
    users: UserRepository = Depends(UserRepository),
) -> ThreadRead:
    """Получение треда по идентификатору."""
    row = await repo.get(thread_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Тред не найден.")
    creator = await users.get(row.created_by_user_id)
    if creator is None:
        raise RuntimeError("Тред ссылается на несуществующего пользователя.")
    return ThreadRead(
        id=row.id,
        channel_id=row.channel_id,
        root_message_id=row.root_message_id,
        title=row.title,
        created_at=row.created_at,
        created_by=UserBrief(id=creator.id, display_name=creator.display_name, avatar_url=creator.avatar_url),
    )

