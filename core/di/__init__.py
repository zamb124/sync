"""Глобальная точка доступа к DI-контейнеру."""

from __future__ import annotations

from typing import Optional

from core.di.container import Container
from core.di.wiring import build_service_container, register_repositories_from_db

_container: Optional[Container] = None


def set_container(container: Container) -> None:
    global _container
    _container = container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError(
            "DI-контейнер не инициализирован. "
            "Инициализируйте контейнер в lifespan() и вызовите set_container()."
        )
    return _container


__all__ = [
    "Container",
    "build_service_container",
    "get_container",
    "register_repositories_from_db",
    "set_container",
]