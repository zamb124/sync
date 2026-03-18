"""Сборка всех роутеров API инженерного чата Sync."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.api import channels, files, git, health, messages, spaces, threads


def get_api_router() -> APIRouter:
    """Возвращает корневой роутер /api со всеми подроутерами."""
    router = APIRouter()

    router.include_router(health.router, tags=["health"])
    router.include_router(spaces.router, prefix="/spaces", tags=["spaces"])
    router.include_router(channels.router, prefix="/channels", tags=["channels"])
    router.include_router(threads.router, prefix="/threads", tags=["threads"])
    router.include_router(messages.router, prefix="/channels", tags=["messages"])
    router.include_router(files.router, prefix="/files", tags=["files"])
    router.include_router(git.router, prefix="/git", tags=["git"])

    return router

