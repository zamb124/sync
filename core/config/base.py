"""Базовый класс настроек и точка доступа к конфигу проекта sync."""

from __future__ import annotations

from typing import Any, Optional, TypeVar

from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import SettingsConfigDict

from core.config.loader import get_project_root, load_merged_config
from core.config.models import (
    AuthConfig,
    LoggingConfig,
    ServerConfig,
    TasksConfig,
    TracingConfig,
)

SettingsT = TypeVar("SettingsT", bound="CoreSettings")


class _MergedJsonConfigSource(PydanticBaseSettingsSource):
    """Источник настроек из объединённых conf*.json файлов."""

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        data = self()
        return data.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        service_name = self.current_state.get("service_name")
        if service_name is None or str(service_name) == "":
            raise RuntimeError("service_name обязателен для загрузки конфигурации.")

        merged = load_merged_config(service_name=str(service_name))
        allowed_keys = set(self.settings_cls.model_fields.keys())
        return {k: v for k, v in merged.items() if k in allowed_keys}


class CoreSettings(PydanticBaseSettings):
    """Базовые настройки, общие для сервисов проекта sync."""

    service_name: str = Field(
        default="",
        description="Имя сервиса, использующего настройки (например, 'sync').",
    )

    server: ServerConfig = Field(
        description="Настройки HTTP‑сервера.",
    )
    tasks: TasksConfig = Field(
        description="Настройки очереди задач TaskIQ.",
    )
    auth: AuthConfig = Field(
        description="Настройки авторизации и permissions.",
    )
    logging: LoggingConfig = Field(
        description="Настройки логирования.",
    )
    tracing: TracingConfig = Field(
        description="Настройки трейсинга.",
    )

    model_config = SettingsConfigDict(
        env_file=str(get_project_root() / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[PydanticBaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Приоритет: init > env > json > secrets > defaults
        return (
            init_settings,
            env_settings,
            _MergedJsonConfigSource(settings_cls),
            file_secret_settings,
        )

    def __init__(self: SettingsT, **data: object) -> None:
        # service_name должен быть определён явно либо через поле класса, либо через аргументы.
        if "service_name" in data:
            svc_name = str(data["service_name"])
            data = {k: v for k, v in data.items() if k != "service_name"}
        else:
            default_service_name = self.__class__.model_fields["service_name"].default
            if default_service_name is None or default_service_name == "":
                raise ValueError("service_name должен быть задан в CoreSettings или его наследнике.")
            svc_name = str(default_service_name)

        # Передаём service_name в init, остальное загрузят sources (env поверх json).
        super().__init__(service_name=svc_name, **data)


_settings_instance: Optional[CoreSettings] = None


def set_settings(settings: CoreSettings) -> None:
    """Устанавливает глобальный инстанс настроек для текущего процесса."""
    global _settings_instance
    _settings_instance = settings


def get_settings() -> CoreSettings:
    """Возвращает текущий инстанс настроек.

    Сервис обязан вызвать set_settings() на этапе старта приложения.
    """
    if _settings_instance is None:
        raise RuntimeError(
            "Настройки не инициализированы. "
            "Вызовите set_settings() при старте приложения перед первым доступом к конфигу."
        )
    return _settings_instance


class _SettingsProxy:
    """Proxy‑объект для удобного доступа к актуальным настройкам."""

    def __getattr__(self, name: str) -> object:
        return getattr(get_settings(), name)

    def __repr__(self) -> str:
        return repr(get_settings())


settings = _SettingsProxy()


__all__ = [
    "CoreSettings",
    "get_settings",
    "set_settings",
    "settings",
]

