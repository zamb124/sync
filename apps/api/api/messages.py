"""Роутеры для работы с сообщениями (Message)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.models.messages import MessageCreate, MessageRead, MessageStatus
from apps.api.src.models.users import UserBrief


router = APIRouter()


@router.get("/{channel_id}/messages", response_model=PaginationResponse[MessageRead])
async def list_messages(
    channel_id: str,
    pagination: PaginationRequest,
) -> PaginationResponse[MessageRead]:
    """Список сообщений канала (заглушка)."""
    return PaginationResponse[MessageRead](items=[], next_cursor=None, prev_cursor=None)


@router.post("/{channel_id}/messages", response_model=MessageRead)
async def send_message(
    channel_id: str,
    payload: MessageCreate,
) -> MessageRead:
    """Отправка сообщения в канал (заглушка)."""
    return MessageRead(
        id="message-example",
        channel_id=channel_id,
        thread_id=payload.thread_id,
        parent_message_id=payload.parent_message_id,
        sender=UserBrief(id="user-example", display_name="User", avatar_url=None),
        status=MessageStatus.SENT,
        sent_at=datetime.utcnow(),
        edited_at=None,
        contents=payload.contents,
    )

