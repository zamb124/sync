"""TaskIQ задачи realtime слоя (общие)."""

from __future__ import annotations

import json

import redis.asyncio as redis

from apps.api.config import ApiSettings
from apps.api.src.db.repositories.channels import ChannelRepository
from apps.api.src.db.repositories.git_resource_refs import GitResourceRefRepository
from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.db.repositories.spaces import SpaceRepository
from apps.api.src.db.repositories.threads import ThreadRepository
from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.realtime.broker import broker
from apps.api.src.realtime.commands import CommandEnvelope
from apps.api.src.realtime.handlers import execute_command
from core.db import Database
from core.logging import get_logger


settings = ApiSettings()
logger = get_logger(__name__)


def _redis() -> redis.Redis:
    return redis.from_url(settings.database.redis_url)


def _database() -> Database:
    return Database(dsn=settings.database.url)


@broker.task
async def handle_command(cmd: dict) -> dict:
    """Выполняет команду и публикует события.

    Возвращает dict совместимый с WsResultFrame (id, ok, result/error).
    """

    command = CommandEnvelope.model_validate(cmd)
    logger.info("task handle_command started: id=%s type=%s actor=%s", command.id, command.type, command.actor_user_id)
    db = _database()
    await db.connect()
    try:
        spaces = SpaceRepository(db)
        channels = ChannelRepository(db)
        threads = ThreadRepository(db)
        messages = MessageRepository(db)
        users = UserRepository(db)
        git_refs = GitResourceRefRepository(db)

        exec_res = await execute_command(
            command,
            spaces=spaces,
            channels=channels,
            threads=threads,
            messages=messages,
            users=users,
            git_refs=git_refs,
        )
    finally:
        await db.close()

    r = _redis()
    try:
        for event in exec_res.events:
            await r.publish(
                "realtime.events",
                json.dumps(event.model_dump(mode="json"), ensure_ascii=False),
            )
    finally:
        await r.aclose()

    if exec_res.ok:
        result_payload = exec_res.result.model_dump(mode="json") if exec_res.result is not None else None
        logger.info("task handle_command ok: id=%s type=%s", command.id, command.type)
        return {"id": command.id, "ok": True, "result": result_payload, "error_code": None, "error_detail": None}
    logger.error("task handle_command failed: id=%s type=%s", command.id, command.type)
    return {
        "id": command.id,
        "ok": False,
        "result": None,
        "error_code": "command_failed",
        "error_detail": "Command failed.",
    }

