"""Модели пользователей для API Sync."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserBrief(BaseModel):
    """Краткая информация о пользователе."""

    id: str = Field(description="Идентификатор пользователя.")
    display_name: str = Field(description="Отображаемое имя.")
    avatar_url: str | None = Field(
        default=None,
        description="URL аватара пользователя.",
    )


class UserRead(UserBrief):
    """Полная модель пользователя для ответов API."""

    external_id: str | None = Field(
        default=None,
        description="Внешний идентификатор (SSO/Git-провайдер).",
    )

