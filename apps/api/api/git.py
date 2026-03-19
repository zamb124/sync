"""Роутеры для работы с абстрактными Git-ресурсами."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.models.git import GitResourceRefCreate, GitResourceRefRead
from apps.api.src.db.repositories.git_resource_refs import GitResourceRefRepository
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.tasks import handle_command
from core.auth.context import require_user
from core.config import settings


router = APIRouter()


@router.post("/resources", response_model=GitResourceRefRead)
async def upsert_git_resource(payload: GitResourceRefCreate) -> GitResourceRefRead:
    """Создание или обновление описания Git-ресурса."""
    user_id = require_user().id
    task = await handle_command.kiq(
        CommandEnvelope(
            id=uuid4().hex,
            actor_user_id=user_id,
            type="git.resources.upsert",
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
    return GitResourceRefRead.model_validate(result)


@router.get("/resources/{git_ref_id}", response_model=GitResourceRefRead)
async def get_git_resource(
    git_ref_id: str,
    repo: GitResourceRefRepository = Depends(GitResourceRefRepository),
) -> GitResourceRefRead:
    """Получение нормализованного Git-ресурса по идентификатору."""
    ref = await repo.get(git_ref_id)
    if ref is None:
        raise HTTPException(status_code=404, detail="Git-ресурс не найден.")
    return ref

