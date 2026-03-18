"""Глобальные фикстуры для тестов проекта sync."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from core.config import CoreSettings, set_settings


@pytest.fixture(scope="session", autouse=False)
def settings() -> Iterator[CoreSettings]:
    """Инициализирует CoreSettings для тестов и возвращает экземпляр.

    В тестах рекомендуется использовать эту фикстуру явно, чтобы зависимость
    от настроек была видимой в сигнатуре.
    """
    cfg = CoreSettings(service_name="sync")
    set_settings(cfg)
    yield cfg

