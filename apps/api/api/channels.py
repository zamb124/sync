"""Роутеры для управления каналами (Channel)."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.src.models.channels import (
    ChannelCreate,
    ChannelMemberAdd,
    ChannelMemberRead,
    ChannelRead,
    ChannelUpdate,
)
from apps.api.src.models.common import PaginationRequest, PaginationResponse


router = APIRouter()


@router.get("/", response_model=PaginationResponse[ChannelRead])
async def list_channels(pagination: PaginationRequest) -> PaginationResponse[ChannelRead]:
    """Список каналов пользователя (заглушка)."""
    return PaginationResponse[ChannelRead](items=[], next_cursor=None, prev_cursor=None)


@router.post("/", response_model=ChannelRead)
async def create_channel(payload: ChannelCreate) -> ChannelRead:
    """Создание канала/чата (заглушка)."""
    from datetime import datetime

    return ChannelRead(
        id="channel-example",
        space_id=payload.space_id,
        type=payload.type,
        name=payload.name,
        is_private=payload.is_private,
        created_at=datetime.utcnow(),
        created_by_user_id="user-example",
    )


@router.patch("/{channel_id}", response_model=ChannelRead)
async def update_channel(channel_id: str, payload: ChannelUpdate) -> ChannelRead:
    """Обновление канала (заглушка)."""
    from datetime import datetime
    from apps.api.src.models.channels import ChannelType

    return ChannelRead(
        id=channel_id,
        space_id=None,
        type=ChannelType.TOPIC,
        name=payload.name or "channel-name",
        is_private=payload.is_private if payload.is_private is not None else False,
        created_at=datetime.utcnow(),
        created_by_user_id="user-example",
    )


@router.post("/{channel_id}/members", response_model=ChannelMemberRead)
async def add_member(channel_id: str, payload: ChannelMemberAdd) -> ChannelMemberRead:
    """Добавление участника в канал (заглушка)."""
    return ChannelMemberRead(user_id=payload.user_id, role=payload.role)

