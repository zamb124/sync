"""Конфигурация проекта sync (базовые модели и загрузка конфигов)."""

from core.config.base import CoreSettings, get_settings, set_settings, settings
from core.config.loader import get_project_root, load_merged_config
from core.config.models import (
    AuthConfig,
    LoggingConfig,
    ServerConfig,
    TasksConfig,
    TracingConfig,
)

__all__ = [
    "CoreSettings",
    "get_settings",
    "set_settings",
    "settings",
    "get_project_root",
    "load_merged_config",
    "ServerConfig",
    "TasksConfig",
    "AuthConfig",
    "LoggingConfig",
    "TracingConfig",
]

