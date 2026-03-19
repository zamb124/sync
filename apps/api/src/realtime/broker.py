"""TaskIQ broker для realtime команд (общий для API и chat_worker)."""

from __future__ import annotations

from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from apps.api.config import ApiSettings
from core.logging import get_logger


settings = ApiSettings()
logger = get_logger(__name__)

if settings.tasks.broker_url.strip() == "":
    raise RuntimeError("tasks.broker_url обязателен.")
if settings.tasks.result_backend.strip() == "":
    raise RuntimeError("tasks.result_backend обязателен.")

logger.info(
    "realtime broker config: broker_url=%s result_backend=%s api_redis=%s",
    settings.tasks.broker_url,
    settings.tasks.result_backend,
    settings.database.redis_url,
)

result_backend = RedisAsyncResultBackend(redis_url=settings.tasks.result_backend)
broker = RedisStreamBroker(url=settings.tasks.broker_url).with_result_backend(result_backend)

