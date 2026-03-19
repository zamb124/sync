"""Роутеры для управления пространствами (Spaces)."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from taskiq.exceptions import TaskiqResultTimeoutError

from apps.api.src.db.repositories.spaces import SpaceRepository
from apps.api.src.models.spaces import SpaceCreate, SpaceRead, SpaceUpdate
from apps.api.src.models.common import PaginationRequest, PaginationResponse
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.tasks import handle_command
from core.config import settings
from core.auth.context import require_user


router = APIRouter()


@router.get("/", response_model=PaginationResponse[SpaceRead])
async def list_spaces(
    repo: SpaceRepository = Depends(SpaceRepository),
    pagination: PaginationRequest = Depends(),
) -> PaginationResponse[SpaceRead]:
    """Список пространств."""
    items = await repo.list(limit=pagination.limit, offset=0)
    return PaginationResponse[SpaceRead](items=items, next_cursor=None, prev_cursor=None)


@router.post("/", response_model=SpaceRead)
async def create_space(
    payload: SpaceCreate,
    repo: SpaceRepository = Depends(SpaceRepository),
) -> SpaceRead:
    """Создание пространства."""
    user_id = require_user().id
    task = await handle_command.kiq(
        CommandEnvelope(
            id=uuid4().hex,
            actor_user_id=user_id,
            type="spaces.create",
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
    return SpaceRead.model_validate(result)


@router.patch("/{space_id}", response_model=SpaceRead)
async def update_space(
    space_id: str,
    payload: SpaceUpdate,
    repo: SpaceRepository = Depends(SpaceRepository),
) -> SpaceRead:
    """Обновление пространства."""
    existing = await repo.get(space_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Пространство не найдено.")

    space = SpaceRead(
        id=existing.id,
        name=payload.name if payload.name is not None else existing.name,
        description=payload.description if payload.description is not None else existing.description,
        created_at=existing.created_at,
        created_by_user_id=existing.created_by_user_id,
    )
    await repo.set(space)
    return space

