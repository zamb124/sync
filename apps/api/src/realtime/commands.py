"""Команды realtime слоя Sync (совместимы с REST DTO)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.models.channels import ChannelCreate, ChannelRead
from apps.api.src.models.git import GitResourceRefCreate, GitResourceRefRead
from apps.api.src.models.messages import MessageCreate, MessageRead
from apps.api.src.models.spaces import SpaceCreate, SpaceRead
from apps.api.src.models.threads import ThreadCreate, ThreadRead


CommandType = Literal[
    "spaces.create",
    "channels.create",
    "threads.create",
    "messages.send",
    "messages.mark_read",
    "git.resources.upsert",
]


class CommandEnvelope(BaseModel):
    """Единая оболочка команды.

    `id` приходит от клиента (uuid). Сервер не генерирует id за клиента.
    """

    id: str = Field(description="UUID команды (client-generated).")
    actor_user_id: str = Field(description="Пользователь, от имени которого выполняется команда.")
    type: CommandType = Field(description="Тип команды.")
    payload: dict = Field(description="Payload команды (совместим с REST DTO).")


class WsCommandFrame(BaseModel):
    """Команда, пришедшая по WebSocket."""

    id: str = Field(description="UUID команды (client-generated).")
    type: CommandType = Field(description="Тип команды.")
    payload: dict = Field(description="Payload команды.")


class WsResultFrame(BaseModel):
    """Результат команды по WebSocket (совместим по данным с REST response DTO)."""

    id: str
    ok: bool
    result: SpaceRead | ChannelRead | ThreadRead | MessageRead | GitResourceRefRead | None = None
    error_code: str | None = None
    error_detail: str | None = None


class SpacesCreatePayload(BaseModel):
    body: SpaceCreate


class ChannelsCreatePayload(BaseModel):
    body: ChannelCreate


class ThreadsCreatePayload(BaseModel):
    body: ThreadCreate


class MessagesSendPayload(BaseModel):
    channel_id: str
    body: MessageCreate


class MessagesMarkReadPayload(BaseModel):
    channel_id: str
    message_id: str


class GitResourcesUpsertPayload(BaseModel):
    body: GitResourceRefCreate

