"""Репозитории для доменных сущностей API-сервиса."""

from core.db import BaseSQLRepository, Database

__all__ = [
    "Database",
    "BaseSQLRepository",
]

