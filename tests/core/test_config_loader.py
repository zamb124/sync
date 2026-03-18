"""Тесты загрузчика конфигурации и CoreSettings."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.config import CoreSettings
from core.config.loader import get_project_root, load_merged_config


def test_get_project_root_points_to_sync_root() -> None:
    """Проверяем, что корень проекта найден и содержит pyproject.toml."""
    root = get_project_root()
    assert (root / "pyproject.toml").exists()
    assert root.name == "sync"


def test_load_merged_config_merges_conf_and_conf_local() -> None:
    """Конфиг должен корректно объединять conf.json и conf.local.json.

    Для сервиса api блок api.database.url из корневых конфигов
    должен оказываться в итоговом словаре как database.url.
    """
    config = load_merged_config(service_name="api")

    assert "database" in config
    assert "tasks" in config
    assert "auth" in config
    assert "server" in config

    # Значения из conf.local.json должны переопределять conf.json.
    assert config["database"]["url"] == "postgresql://sync_user:sync_admin@localhost:5435/sync_db"
    assert config["database"]["redis_url"] == "redis://localhost:6381/0"
    assert config["tasks"]["broker_url"] == "redis://localhost:6381/1"


def test_load_merged_config_includes_service_specific_files(tmp_path: Path) -> None:
    """Сервисные конфиги в apps/<service>/conf*.json должны учитываться."""
    project_root = get_project_root()
    service_dir = project_root / "apps" / "test_service"
    service_dir.mkdir(parents=True, exist_ok=True)

    try:
        service_conf = service_dir / "conf.json"
        service_conf.write_text(
            """
{
  "server": {
    "port": 9000
  }
}
""".strip(),
            encoding="utf-8",
        )

        service_local_conf = service_dir / "conf.local.json"
        service_local_conf.write_text(
            """
{
  "server": {
    "debug": false
  }
}
""".strip(),
            encoding="utf-8",
        )

        config = load_merged_config(service_name="test_service")

        assert config["server"]["port"] == 9000
        assert config["server"]["debug"] is False
    finally:
        if service_conf.exists():
            service_conf.unlink()
        if service_local_conf.exists():
            service_local_conf.unlink()
        # Папку apps/test_service оставляем, чтобы не трогать структуру проекта.


@pytest.mark.parametrize(
    "env_key,field_path,expected_value",
    [
        ("SERVER__PORT", ("server", "port"), "8100"),
        ("AUTH__JWT_SECRET", ("auth", "jwt_secret"), "env-secret-key"),
    ],
)
def test_core_settings_reads_values_from_env_and_overrides_json(
    env_key: str,
    field_path: tuple[str, str],
    expected_value: str,
) -> None:
    """CoreSettings должен учитывать значения из окружения и переопределять JSON-конфиг."""
    env_backup = dict(os.environ)

    try:
        os.environ[env_key] = expected_value

        settings = CoreSettings(service_name="sync")

        section_name, field_name = field_path
        section = getattr(settings, section_name)
        value = getattr(section, field_name)

        if isinstance(value, int):
            assert str(value) == expected_value
        else:
            assert value == expected_value
    finally:
        os.environ.clear()
        os.environ.update(env_backup)

