"""Глобальный доступ к DI контейнеру API сервиса.

Использование:
    from apps.api.container import get_container
    repo = get_container().resolve(SpaceRepository)

или:
    from apps.api.container import container
    repo = container.resolve(SpaceRepository)
"""

from __future__ import annotations

from typing import Optional, TypeVar

from apps.api.config import ApiSettings
from apps.api.src.db.repositories import (
    ChannelRepository,
    MessageRepository,
    SpaceRepository,
    ThreadRepository,
    UserRepository,
)
from core.db import Database
from core.di import Container as CoreContainer
from core.di import build_service_container
from core.di import set_container as set_core_container


_container: Optional[CoreContainer] = None
T = TypeVar("T")


def build_container(settings: ApiSettings) -> CoreContainer:
    repositories = [
        SpaceRepository,
        ChannelRepository,
        ThreadRepository,
        MessageRepository,
        UserRepository,
    ]
    return build_service_container(
        db_type=Database,
        db_factory=lambda: Database(dsn=settings.database.url),
        repositories=repositories,
    )


def set_container(container: CoreContainer) -> None:
    """Устанавливает DI контейнер для процесса API сервиса."""

    global _container
    _container = container
    # Дублируем в core для общего кода, который использует core.di.get_container().
    set_core_container(container)


def get_container() -> CoreContainer:
    """Возвращает DI контейнер текущего процесса."""

    if _container is None:
        raise RuntimeError(
            "DI контейнер apps.api не инициализирован. "
            "Проверьте, что set_container() вызывается в lifespan()."
        )
    return _container


class _ContainerProxy:
    """Proxy для удобного доступа: apps.api.container.container.resolve(...)."""

    def resolve(self, key: type[T]) -> T:
        return get_container().resolve(key)

    def __repr__(self) -> str:
        return repr(get_container())


container = _ContainerProxy()


__all__ = ["build_container", "container", "get_container", "set_container"]

