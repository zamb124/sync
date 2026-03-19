"""Утилиты wiring для сервисов.

Цель: максимум простоты в apps/* при регистрации типовых зависимостей.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from core.di.container import Container

DbT = TypeVar("DbT")


def build_service_container(
    *,
    db_type: type[DbT],
    db_factory: Callable[[], DbT],
    repositories: Iterable[type[Any]],
) -> Container:
    """Собирает контейнер сервиса: singleton DB + репозитории Repo(DB).

    Сервису остаётся только передать db_factory и список репозиториев.
    """

    container = Container()
    container.register_factory(db_type, lambda c: db_factory(), cache=True)
    register_repositories_from_db(container, db_type=db_type, repositories=repositories)
    return container


def register_repositories_from_db(
    container: Container,
    *,
    db_type: type[Any],
    repositories: Iterable[type[Any]],
) -> None:
    """Регистрирует репозитории, которые создаются как Repo(Database).

    Zero-Guess: если класс репозитория не соответствует конвенции (ровно один
    обязательный аргумент конструктора помимо self), выбрасываем RuntimeError.
    """

    for repo_type in repositories:
        _ensure_repo_ctor_is_repo_db(repo_type)
        container.register_factory(
            repo_type,
            lambda c, rt=repo_type: rt(c.resolve(db_type)),
            cache=False,
        )


def _ensure_repo_ctor_is_repo_db(repo_type: type[Any]) -> None:
    try:
        sig = inspect.signature(repo_type.__init__)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Не удалось проанализировать конструктор репозитория: {repo_type!r}") from exc

    params = list(sig.parameters.values())
    # ожидаем: (self, database, *optional...)
    if not params:
        raise RuntimeError(f"Некорректный конструктор репозитория: {repo_type!r}")

    # выкидываем self
    params = params[1:]

    required = [
        p
        for p in params
        if p.default is inspect._empty
        and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]

    if len(required) == 1:
        return

    if len(required) == 0:
        if not params:
            raise RuntimeError(f"Некорректный конструктор репозитория: {repo_type!r}")
        first = params[0]
        if first.name != "database":
            raise RuntimeError(
                "Репозиторий должен иметь конструктор вида Repo(database: Database). "
                f"Получено: {repo_type!r} с первым параметром: {first.name!r}"
            )
        return

    if len(required) != 1:
        raise RuntimeError(
            "Репозиторий должен иметь конструктор вида Repo(database: Database). "
            f"Получено: {repo_type!r} с обязательными параметрами: {[p.name for p in required]!r}"
        )

