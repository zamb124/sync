"""Точка входа chat_worker.

Запуск:
    uv run taskiq worker apps.chat_worker.broker:broker
"""

from __future__ import annotations

# Импорт tasks нужен для регистрации @broker.task
from apps.api.src.realtime import tasks  # noqa: F401

