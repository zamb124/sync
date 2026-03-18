"""Health-check эндпоинты API."""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Проверка живости сервиса."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    """Проверка готовности сервиса (пока всегда ok)."""
    return {"status": "ready"}

