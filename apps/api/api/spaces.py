"""Роутеры для управления пространствами (Spaces)."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.src.models.spaces import SpaceCreate, SpaceRead, SpaceUpdate
from apps.api.src.models.common import PaginationRequest, PaginationResponse


router = APIRouter()


@router.get("/", response_model=PaginationResponse[SpaceRead])
async def list_spaces(pagination: PaginationRequest) -> PaginationResponse[SpaceRead]:
    """Список пространств пользователя (заглушка без доступа к БД)."""
    return PaginationResponse[SpaceRead](items=[], next_cursor=None, prev_cursor=None)


@router.post("/", response_model=SpaceRead)
async def create_space(payload: SpaceCreate) -> SpaceRead:
    """Создание пространства (заглушка)."""
    return SpaceRead(
        id="space-example",
        name=payload.name,
        description=payload.description,
        created_at=__import__("datetime").datetime.utcnow(),
        created_by_user_id="user-example",
    )


@router.patch("/{space_id}", response_model=SpaceRead)
async def update_space(space_id: str, payload: SpaceUpdate) -> SpaceRead:
    """Обновление пространства (заглушка)."""
    return SpaceRead(
        id=space_id,
        name=payload.name or "space-name",
        description=payload.description,
        created_at=__import__("datetime").datetime.utcnow(),
        created_by_user_id="user-example",
    )

