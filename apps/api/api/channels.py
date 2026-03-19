"""Роутеры для управления каналами (Channel)."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from taskiq.exceptions import TaskiqResultTimeoutError

from apps.api.src.models.channels import (
    ChannelCreate,
    ChannelMemberAdd,
    ChannelMemberRead,
    ChannelRead,
    ChannelType,
    ChannelUpdate,
)
from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.db.repositories.channels import ChannelRepository
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.tasks import handle_command
from core.config import settings
from core.auth.context import require_user


router = APIRouter()


@router.get("/", response_model=PaginationResponse[ChannelRead])
async def list_channels(
    repo: ChannelRepository = Depends(ChannelRepository),
    pagination: PaginationRequest = Depends(),
) -> PaginationResponse[ChannelRead]:
    """Список каналов."""
    items = await repo.list(limit=pagination.limit, offset=0)
    return PaginationResponse[ChannelRead](items=items, next_cursor=None, prev_cursor=None)


@router.post("/", response_model=ChannelRead)
async def create_channel(
    payload: ChannelCreate,
    repo: ChannelRepository = Depends(ChannelRepository),
) -> ChannelRead:
    """Создание канала/чата."""
    user_id = require_user().id
    if payload.type == ChannelType.TOPIC:
        if payload.space_id is None:
            raise HTTPException(status_code=422, detail="Для topic обязателен space_id.")
        if payload.name is None:
            raise HTTPException(status_code=422, detail="Для topic обязателен name.")
    task = await handle_command.kiq(
        CommandEnvelope(
            id=uuid4().hex,
            actor_user_id=user_id,
            type="channels.create",
            payload={"body": payload.model_dump()},
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
    return ChannelRead.model_validate(result)


@router.patch("/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: str,
    payload: ChannelUpdate,
    repo: ChannelRepository = Depends(ChannelRepository),
) -> ChannelRead:
    """Обновление канала."""
    existing = await repo.get(channel_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Канал не найден.")

    channel = ChannelRead(
        id=existing.id,
        space_id=existing.space_id,
        type=existing.type,
        name=payload.name if payload.name is not None else existing.name,
        is_private=payload.is_private if payload.is_private is not None else existing.is_private,
        created_at=existing.created_at,
        created_by_user_id=existing.created_by_user_id,
    )
    await repo.set(channel)
    return channel


@router.post("/{channel_id}/members", response_model=ChannelMemberRead)
async def add_member(
    channel_id: str,
    payload: ChannelMemberAdd,
    repo: ChannelRepository = Depends(ChannelRepository),
) -> ChannelMemberRead:
    """Добавление участника в канал."""
    channel = await repo.get(channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Канал не найден.")

    await repo.upsert_member(channel_id, payload.user_id, payload.role)
    return ChannelMemberRead(user_id=payload.user_id, role=payload.role)

