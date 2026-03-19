"""Глобальные фикстуры для тестов проекта sync."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from core.config import CoreSettings, set_settings
from tests.fixtures.api_server_manager import ApiServer, ApiServerManager
from tests.fixtures.auth_fixture import UserAuth, create_user_and_jwt
from tests.fixtures.chat_worker_manager import ChatWorker, ChatWorkerManager
from tests.fixtures.test_infra_manager import InfraManager, InfraRuntime


@pytest.fixture(scope="session", autouse=False)
def settings() -> Iterator[CoreSettings]:
    """Инициализирует CoreSettings для тестов и возвращает экземпляр.

    В тестах рекомендуется использовать эту фикстуру явно, чтобы зависимость
    от настроек была видимой в сигнатуре.
    """
    cfg = CoreSettings(service_name="sync")
    set_settings(cfg)
    yield cfg


@pytest.fixture(scope="session", autouse=False)
def test_env() -> Iterator[None]:
    """Настраивает окружение для интеграционных тестов.

    Тесты используют отдельное docker-compose.test.yml окружение.
    """
    env_backup = dict(os.environ)
    try:
        os.environ["API__DATABASE__URL"] = "postgresql://sync_user:sync_admin@localhost:55432/sync_test_db"
        os.environ["API__DATABASE__REDIS_URL"] = "redis://localhost:56379/0"
        os.environ["API__TASKS__BROKER_URL"] = "redis://localhost:56379/0"
        os.environ["API__TASKS__RESULT_BACKEND"] = "redis://localhost:56379/0"
        os.environ["API__TASKS__DEFAULT_TASK_TIMEOUT"] = "10"
        os.environ["AUTH__JWT_SECRET"] = "test-jwt-secret"
        yield
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


@pytest.fixture(scope="session", autouse=True)
def test_infra(test_env: None) -> Iterator[InfraRuntime]:
    manager = InfraManager(env=dict(os.environ))
    infra = manager.start(timeout_s=60.0)
    try:
        yield infra
    finally:
        manager.stop()


@pytest.fixture(scope="session")
def chat_worker(test_env: None, test_infra: InfraRuntime) -> Iterator[ChatWorker]:
    manager = ChatWorkerManager(env=dict(os.environ))
    worker = manager.start()
    try:
        yield worker
    finally:
        manager.stop()


@pytest.fixture(scope="session")
def api_server(test_env: None, test_infra: InfraRuntime, chat_worker: ChatWorker) -> Iterator[ApiServer]:
    manager = ApiServerManager(env=os.environ)
    server = manager.start(timeout_s=30.0)
    try:
        yield server
    finally:
        manager.stop()


@pytest.fixture()
def user_auth(api_server: ApiServer) -> UserAuth:
    return create_user_and_jwt(base_url=api_server.base_url)

