"""Роутеры для работы с абстрактными Git-ресурсами."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.src.models.git import GitResourceRefCreate, GitResourceRefRead


router = APIRouter()


@router.post("/resources", response_model=GitResourceRefRead)
async def upsert_git_resource(payload: GitResourceRefCreate) -> GitResourceRefRead:
    """Создание или обновление описания Git-ресурса (заглушка)."""
    return GitResourceRefRead(
        id="gitref-example",
        provider=payload.provider,
        kind=payload.kind,
        project_key=payload.project_key,
        external_id=payload.external_id,
        url=payload.url,
        extra=payload.extra or {},
    )


@router.get("/resources/{git_ref_id}", response_model=GitResourceRefRead)
async def get_git_resource(git_ref_id: str) -> GitResourceRefRead:
    """Получение нормализованного Git-ресурса по идентификатору (заглушка)."""
    return GitResourceRefRead(
        id=git_ref_id,
        provider="gitlab",
        kind="merge_request",  # type: ignore[arg-type]
        project_key="group/project",
        external_id="123",
        url="https://gitlab.example.com/group/project/-/merge_requests/123",
        extra={},
    )

