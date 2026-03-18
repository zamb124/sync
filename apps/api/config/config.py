"""Специализированные настройки для API-сервиса."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.config import CoreSettings


class ApiDatabaseConfig(BaseModel):
    """Конфигурация подключения API-сервиса к PostgreSQL и Redis."""

    url: str = Field(description="Полный DSN для PostgreSQL (обязателен).")
    redis_url: str = Field(description="Полный DSN для Redis (обязателен).")


class ApiSettings(CoreSettings):
    """Настройки FastAPI-сервиса API.

    Наследуется от общих CoreSettings и может добавлять поля,
    специфичные для API-слоя (лимиты, флаги, интеграции и т.п.).
    """

    service_name: str = Field(
        default="api",
        description="Имя сервиса для загрузки сервисных конфигов из apps/api.",
    )

    database: ApiDatabaseConfig = Field(
        description="Настройки соединения API-сервиса с PostgreSQL и Redis.",
    )

