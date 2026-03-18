"""Роутеры для работы с тредами (Thread)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from apps.api.src.models.threads import ThreadCreate, ThreadRead, ThreadSummary
from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.models.users import UserBrief


router = APIRouter()


@router.get("/", response_model=PaginationResponse[ThreadSummary])
async def list_threads(pagination: PaginationRequest) -> PaginationResponse[ThreadSummary]:
    """Список тредов (заглушка)."""
    return PaginationResponse[ThreadSummary](items=[], next_cursor=None, prev_cursor=None)


@router.post("/", response_model=ThreadRead)
async def create_thread(payload: ThreadCreate) -> ThreadRead:
    """Создание треда (заглушка)."""
    return ThreadRead(
        id="thread-example",
        channel_id="channel-example",
        root_message_id=payload.root_message_id,
        title=payload.title,
        created_at=datetime.utcnow(),
        created_by=UserBrief(id="user-example", display_name="User", avatar_url=None),
    )


@router.get("/{thread_id}", response_model=ThreadRead)
async def get_thread(thread_id: str) -> ThreadRead:
    """Получение треда по идентификатору (заглушка)."""
    return ThreadRead(
        id=thread_id,
        channel_id="channel-example",
        root_message_id="message-root",
        title=None,
        created_at=datetime.utcnow(),
        created_by=UserBrief(id="user-example", display_name="User", avatar_url=None),
    )

