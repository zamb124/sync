"""Загрузка и объединение конфигов для проекта sync.

Zero‑Guess:
- корневой conf.json обязателен;
- conf.local.json опционален, но если его нет, это осознанное решение;
- никакой магии с путями и скрытыми фолбеками.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv


def _load_json_config(config_path: Path, *, required: bool) -> Dict[str, Any]:
    """Загружает JSON‑конфиг из файла.

    Если required=True и файл отсутствует или не читается — выбрасывает исключение.
    Для необязательных файлов отсутствие считается нормальной ситуацией.
    """
    if not config_path.exists():
        if required:
            raise FileNotFoundError(f"Обязательный файл конфигурации не найден: {config_path}")
        return {}

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        if required:
            raise RuntimeError(f"Не удалось прочитать файл конфигурации: {config_path}") from exc
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON в файле конфигурации: {config_path}") from exc


def _merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Рекурсивно объединяет два словаря конфигурации.

    Значения из override_config всегда имеют приоритет.
    """
    result: Dict[str, Any] = dict(base_config)

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def get_project_root() -> Path:
    """Возвращает корневую директорию проекта.

    Поиском вверх от текущего файла на ограниченное число уровней.
    Корень определяется наличием pyproject.toml или .git.
    """
    current = Path(__file__).resolve().parent

    for _ in range(10):
        pyproject = current / "pyproject.toml"
        git_dir = current / ".git"
        if pyproject.exists() or git_dir.exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise RuntimeError("Не удалось определить корень проекта (pyproject.toml или .git не найдены).")


def _get_config_paths(service_name: str | None) -> List[Path]:
    """Формирует упорядоченный список путей конфигурации.

    Порядок:
    1. <root>/conf.json (обязательный)
    2. <root>/conf.local.json (опциональный)
    3. <root>/apps/<service_name>/conf.json (опциональный, если задан service_name)
    4. <root>/apps/<service_name>/conf.local.json (опциональный, если задан service_name)
    """
    project_root = get_project_root()
    paths: List[Path] = [
        project_root / "conf.json",
        project_root / "conf.local.json",
    ]

    if service_name is not None and service_name != "":
        service_dir = project_root / "apps" / service_name
        paths.append(service_dir / "conf.json")
        paths.append(service_dir / "conf.local.json")

    return paths


def load_merged_config(service_name: str | None) -> Dict[str, Any]:
    """Загружает и объединяет конфиги для сервиса.

    Всегда требует наличия корневого conf.json.
    Локальные и сервисные конфиги, если существуют, переопределяют значения.
    """
    project_root = get_project_root()
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)

    merged: Dict[str, Any] = {}
    paths = _get_config_paths(service_name)

    for index, config_path in enumerate(paths):
        # Первый файл — всегда корневой conf.json и он обязателен.
        required = index == 0
        config_part = _load_json_config(config_path, required=required)
        if config_part:
            merged = _merge_configs(merged, config_part)

    if service_name is not None and service_name != "":
        service_block = merged.get(service_name)
        if isinstance(service_block, dict):
            merged = _merge_configs(merged, service_block)

    return merged


__all__ = [
    "get_project_root",
    "load_merged_config",
]

