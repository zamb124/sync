"""Роутеры для работы с сообщениями (Message)."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from taskiq.exceptions import TaskiqResultTimeoutError

from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.models.messages import MessageCreate, MessageRead, MessageStatus
from apps.api.src.models.users import UserBrief
from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.tasks import handle_command
from core.config import settings
from core.auth.context import require_user


router = APIRouter()


@router.get("/{channel_id}/messages", response_model=PaginationResponse[MessageRead])
async def list_messages(
    channel_id: str,
    pagination: PaginationRequest = Depends(),
    repo: MessageRepository = Depends(MessageRepository),
    users: UserRepository = Depends(UserRepository),
) -> PaginationResponse[MessageRead]:
    """Список сообщений канала."""
    rows = await repo.list_by_channel(channel_id, limit=pagination.limit, offset=0)
    items: list[MessageRead] = []
    for row in rows:
        contents = await repo.list_contents(row.id)
        sender = await users.get(row.sender_user_id)
        if sender is None:
            raise RuntimeError("Сообщение ссылается на несуществующего пользователя.")
        items.append(
            MessageRead(
                id=row.id,
                channel_id=row.channel_id,
                thread_id=row.thread_id,
                parent_message_id=row.parent_message_id,
                sender=UserBrief(id=sender.id, display_name=sender.display_name, avatar_url=sender.avatar_url),
                status=MessageStatus(row.status),
                sent_at=row.sent_at,
                edited_at=row.edited_at,
                contents=[{"type": c.type, "data": c.data, "order": c.order} for c in contents],
            )
        )
    return PaginationResponse[MessageRead](items=items, next_cursor=None, prev_cursor=None)


@router.post("/{channel_id}/messages", response_model=MessageRead)
async def send_message(
    channel_id: str,
    payload: MessageCreate,
    repo: MessageRepository = Depends(MessageRepository),
    users: UserRepository = Depends(UserRepository),
) -> MessageRead:
    """Отправка сообщения в канал."""
    user_id = require_user().id
    sender = await users.get(user_id)
    if sender is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    task = await handle_command.kiq(
        CommandEnvelope(
            id=uuid4().hex,
            actor_user_id=user_id,
            type="messages.send",
            payload={"channel_id": channel_id, "body": payload.model_dump()},
        ).model_dump()
    )
    try:
        res = await task.wait_result(timeout=settings.tasks.default_task_timeout)
    except TaskiqResultTimeoutError:
        raise HTTPException(status_code=504, detail="Timeout выполнения команды.")
    if res.is_err:
        raise RuntimeError(str(res.error))
    if not res.return_value.get("ok"):
        raise HTTPException(status_code=422, detail=res.return_value.get("error_detail") or "Ошибка команды.")
    result = res.return_value.get("result")
    if result is None:
        raise RuntimeError("Команда вернула пустой результат.")
    return MessageRead.model_validate(result)

