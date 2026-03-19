"""Настройки и утилиты логирования для проекта sync."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Возвращает logger для модуля.

    Конфигурацией уровня/хендлеров управляет uvicorn/сервис.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    return logging.getLogger(name)


__all__ = ["get_logger"]

