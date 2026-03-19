"""Тесты DI контейнера core."""

from __future__ import annotations

import pytest

from core.di import Container
from core.di.wiring import build_service_container


class DepA:
    def __init__(self) -> None:
        self.value = "a"


class DepB:
    def __init__(self, dep_a: DepA) -> None:
        self.dep_a = dep_a


class RepoOk:
    def __init__(self, dep_a: DepA) -> None:
        self.dep_a = dep_a


class RepoBad:
    def __init__(self, dep_a: DepA, other: str) -> None:
        self.dep_a = dep_a
        self.other = other


def test_container_register_instance_and_resolve() -> None:
    c = Container()
    a = DepA()
    c.register_instance(DepA, a)
    assert c.resolve(DepA) is a


def test_container_register_factory_cache_true() -> None:
    c = Container()
    c.register_factory(DepA, lambda _: DepA(), cache=True)
    a1 = c.resolve(DepA)
    a2 = c.resolve(DepA)
    assert a1 is a2


def test_container_register_factory_cache_false() -> None:
    c = Container()
    c.register_factory(DepA, lambda _: DepA(), cache=False)
    a1 = c.resolve(DepA)
    a2 = c.resolve(DepA)
    assert a1 is not a2


def test_container_resolve_not_registered_raises() -> None:
    c = Container()
    with pytest.raises(RuntimeError, match="не зарегистрирована"):
        c.resolve(DepA)


def test_build_service_container_registers_db_and_repos() -> None:
    container = build_service_container(
        db_type=DepA,
        db_factory=DepA,
        repositories=[RepoOk],
    )
    repo = container.resolve(RepoOk)
    assert isinstance(repo, RepoOk)
    assert isinstance(repo.dep_a, DepA)


def test_build_service_container_rejects_repo_with_extra_required_params() -> None:
    with pytest.raises(RuntimeError, match="Repo\\(database"):
        build_service_container(
            db_type=DepA,
            db_factory=DepA,
            repositories=[RepoBad],
        )

