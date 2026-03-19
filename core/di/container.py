"""Простой DI-контейнер для сервисов sync.

Core не должен импортировать apps. Сервисы сами регистрируют свои зависимости.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class _Factory(Generic[T]):
    factory: Callable[["Container"], T]
    cache: bool


class Container:
    """DI-контейнер с регистрацией по типам."""

    def __init__(self) -> None:
        self._instances: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], _Factory[Any]] = {}

    def register_instance(self, key: type[T], value: T) -> None:
        if key in self._instances or key in self._factories:
            raise RuntimeError(f"Зависимость уже зарегистрирована: {key!r}")
        self._instances[key] = value

    def register_factory(
        self,
        key: type[T],
        factory: Callable[["Container"], T],
        *,
        cache: bool,
    ) -> None:
        if key in self._instances or key in self._factories:
            raise RuntimeError(f"Зависимость уже зарегистрирована: {key!r}")
        self._factories[key] = _Factory(factory=factory, cache=cache)

    def resolve(self, key: type[T]) -> T:
        if key in self._instances:
            return self._instances[key]

        factory_cfg = self._factories.get(key)
        if factory_cfg is None:
            raise RuntimeError(f"Зависимость не зарегистрирована в контейнере: {key!r}")

        value = factory_cfg.factory(self)
        if factory_cfg.cache:
            self._instances[key] = value
        return value