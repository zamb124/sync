"""WebSocket endpoint realtime слоя."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from taskiq.exceptions import TaskiqResultTimeoutError

from apps.api.config import ApiSettings
from apps.api.src.realtime.commands import CommandEnvelope, WsCommandFrame, WsResultFrame
from apps.api.src.realtime.tasks import handle_command
from core.auth.context import reset_current_user, set_current_user
from core.auth.models import AuthenticatedUser
from core.auth.jwt import decode_and_verify
from core.logging import get_logger


settings = ApiSettings()
logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Connection:
    user_id: str
    websocket: WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._by_user: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._by_user.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        ws_set = self._by_user.get(user_id)
        if ws_set is None:
            return
        ws_set.discard(websocket)
        if not ws_set:
            self._by_user.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        ws_set = self._by_user.get(user_id)
        if not ws_set:
            return
        text = json.dumps(payload, ensure_ascii=False)
        for ws in list(ws_set):
            try:
                await ws.send_text(text)
            except Exception:
                logger.exception("ws send_to_user failed: user_id=%s", user_id)
                ws_set.discard(ws)
        if not ws_set:
            self._by_user.pop(user_id, None)

    async def broadcast(self, payload: dict) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for user_id, ws_set in list(self._by_user.items()):
            for ws in list(ws_set):
                try:
                    await ws.send_text(text)
                except Exception:
                    logger.exception("ws broadcast send failed: user_id=%s", user_id)
                    ws_set.discard(ws)
            if not ws_set:
                self._by_user.pop(user_id, None)


manager = ConnectionManager()


class PubSubFanout:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._redis: redis.Redis | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._redis = redis.from_url(settings.database.redis_url)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        task = self._task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            if self._redis is not None:
                await self._redis.aclose()
                self._redis = None

    async def _run(self) -> None:
        r = self._redis
        if r is None:
            raise RuntimeError("Redis не инициализирован.")
        async with r.pubsub() as pubsub:
            await pubsub.subscribe("realtime.events")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message is None:
                    continue
                data_raw = message.get("data")
                if not isinstance(data_raw, (bytes, bytearray)):
                    raise RuntimeError("Некорректный тип pubsub message.data.")
                try:
                    event = json.loads(data_raw.decode("utf-8"))
                except Exception:
                    logger.exception("pubsub event decode failed")
                    continue
                try:
                    await manager.broadcast(event)
                except Exception:
                    logger.exception("pubsub broadcast failed")


fanout = PubSubFanout()


async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if token is None or token.strip() == "":
        await websocket.close(code=1008)
        return
    claims = decode_and_verify(token, secret=settings.auth.jwt_secret, algorithm=settings.auth.jwt_algorithm)
    auth_user = AuthenticatedUser(id=claims.sub, claims=claims)
    ctx_token = set_current_user(auth_user)
    try:
        await manager.connect(auth_user.id, websocket)
        while True:
            raw = await websocket.receive_text()
            frame = WsCommandFrame.model_validate_json(raw)
            logger.info("ws cmd received: user_id=%s id=%s type=%s", auth_user.id, frame.id, frame.type)
            cmd = CommandEnvelope(
                id=frame.id,
                actor_user_id=auth_user.id,
                type=frame.type,
                payload=frame.payload,
            )
            task = await handle_command.kiq(cmd.model_dump())
            logger.info("ws cmd queued: id=%s", frame.id)
            try:
                res = await task.wait_result(timeout=settings.tasks.default_task_timeout)
            except TaskiqResultTimeoutError as exc:
                logger.error("ws cmd timeout: id=%s timeout=%s", frame.id, exc.timeout)
                out = WsResultFrame(
                    id=frame.id,
                    ok=False,
                    result=None,
                    error_code="timeout",
                    error_detail=f"Task timeout: {exc.timeout}",
                )
                await websocket.send_text(out.model_dump_json())
                continue
            try:
                if res.is_err:
                    logger.error("ws cmd failed: id=%s error=%s", frame.id, res.error)
                    out = WsResultFrame(
                        id=frame.id,
                        ok=False,
                        result=None,
                        error_code="task_error",
                        error_detail=str(res.error),
                    )
                else:
                    logger.info("ws cmd ok: id=%s", frame.id)
                    out = WsResultFrame.model_validate({"id": frame.id, **res.return_value})
                await websocket.send_text(out.model_dump_json())
                logger.info("ws cmd result sent: id=%s ok=%s", frame.id, out.ok)
            except Exception as exc:
                logger.exception("ws cmd result build/send failed: id=%s exc=%r", frame.id, exc)
                out = WsResultFrame(
                    id=frame.id,
                    ok=False,
                    result=None,
                    error_code="ws_internal_error",
                    error_detail=str(exc),
                )
                await websocket.send_text(out.model_dump_json())
    except WebSocketDisconnect:
        manager.disconnect(auth_user.id, websocket)
    finally:
        reset_current_user(ctx_token)

