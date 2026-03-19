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

    email: str = Field(description="Email пользователя (уникальный).")
    username: str = Field(description="Username пользователя (уникальный).")
    first_name: str = Field(description="Имя пользователя.")
    last_name: str = Field(description="Фамилия пользователя.")
    is_active: bool = Field(description="Флаг активности пользователя.")
    external_id: str | None = Field(
        default=None,
        description="Внешний идентификатор (SSO/Git-провайдер).",
    )

