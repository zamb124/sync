"""Бизнес-обработка realtime команд (исполняется в chat_worker)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.src.db.repositories.channels import ChannelRepository
from apps.api.src.db.repositories.git_resource_refs import GitResourceRefRepository
from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.db.repositories.spaces import SpaceRepository
from apps.api.src.db.repositories.threads import ThreadRepository
from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.models.channels import ChannelRead, ChannelType
from apps.api.src.models.git import GitResourceRefRead
from apps.api.src.models.messages import MessageRead, MessageStatus
from apps.api.src.models.spaces import SpaceRead
from apps.api.src.models.threads import ThreadRead, ThreadRow
from apps.api.src.models.users import UserBrief
from apps.api.src.realtime.commands import (
    ChannelsCreatePayload,
    CommandEnvelope,
    GitResourcesUpsertPayload,
    MessagesMarkReadPayload,
    MessagesSendPayload,
    SpacesCreatePayload,
    ThreadsCreatePayload,
)
from apps.api.src.realtime.events import (
    MessageStatusChangedPayload,
    RealtimeEvent,
    event_channel_created,
    event_git_resource_upserted,
    event_message_created,
    event_message_status_changed,
    event_space_created,
    event_thread_created,
)


class CommandExecutionResult:
    def __init__(self, *, ok: bool, result: object | None, events: list[RealtimeEvent]) -> None:
        self.ok = ok
        self.result = result
        self.events = events


async def execute_command(
    cmd: CommandEnvelope,
    *,
    spaces: SpaceRepository,
    channels: ChannelRepository,
    threads: ThreadRepository,
    messages: MessageRepository,
    users: UserRepository,
    git_refs: GitResourceRefRepository,
) -> CommandExecutionResult:
    if cmd.type == "spaces.create":
        payload = SpacesCreatePayload.model_validate(cmd.payload)
        space = await _create_space(payload.body, actor_user_id=cmd.actor_user_id, spaces=spaces)
        return CommandExecutionResult(ok=True, result=space, events=[event_space_created(space)])

    if cmd.type == "channels.create":
        payload = ChannelsCreatePayload.model_validate(cmd.payload)
        channel = await _create_channel(payload.body, actor_user_id=cmd.actor_user_id, channels=channels)
        return CommandExecutionResult(ok=True, result=channel, events=[event_channel_created(channel)])

    if cmd.type == "threads.create":
        payload = ThreadsCreatePayload.model_validate(cmd.payload)
        thread = await _create_thread(
            payload.body,
            actor_user_id=cmd.actor_user_id,
            threads=threads,
            messages=messages,
            users=users,
        )
        return CommandExecutionResult(ok=True, result=thread, events=[event_thread_created(thread)])

    if cmd.type == "messages.send":
        payload = MessagesSendPayload.model_validate(cmd.payload)
        message = await _send_message(
            payload.channel_id,
            payload.body,
            actor_user_id=cmd.actor_user_id,
            messages=messages,
            users=users,
        )
        return CommandExecutionResult(ok=True, result=message, events=[event_message_created(message)])

    if cmd.type == "messages.mark_read":
        payload = MessagesMarkReadPayload.model_validate(cmd.payload)
        # MVP: не храним per-user read, только публикуем событие.
        event = event_message_status_changed(
            payload.channel_id,
            MessageStatusChangedPayload(message_id=payload.message_id, status=MessageStatus.READ),
        )
        return CommandExecutionResult(ok=True, result=None, events=[event])

    if cmd.type == "git.resources.upsert":
        payload = GitResourcesUpsertPayload.model_validate(cmd.payload)
        ref = await _upsert_git_resource(payload.body, git_refs=git_refs)
        return CommandExecutionResult(ok=True, result=ref, events=[event_git_resource_upserted(ref)])

    raise RuntimeError(f"Неизвестный тип команды: {cmd.type!r}.")


async def _create_space(
    body,
    *,
    actor_user_id: str,
    spaces: SpaceRepository,
) -> SpaceRead:
    space = SpaceRead(
        id=uuid4().hex,
        name=body.name,
        description=body.description,
        created_at=datetime.now(tz=UTC),
        created_by_user_id=actor_user_id,
    )
    await spaces.set(space)
    return space


async def _create_channel(
    body,
    *,
    actor_user_id: str,
    channels: ChannelRepository,
) -> ChannelRead:
    if body.type == ChannelType.TOPIC:
        if body.space_id is None:
            raise ValueError("Для topic обязателен space_id.")
        if body.name is None:
            raise ValueError("Для topic обязателен name.")
    channel = ChannelRead(
        id=uuid4().hex,
        space_id=body.space_id,
        type=body.type,
        name=body.name,
        is_private=body.is_private,
        created_at=datetime.now(tz=UTC),
        created_by_user_id=actor_user_id,
    )
    await channels.set(channel)
    await channels.add_member_if_missing(channel.id, actor_user_id, "owner")
    if body.member_ids is not None:
        for member_id in body.member_ids:
            await channels.add_member_if_missing(channel.id, member_id, "member")
    return channel


async def _send_message(
    channel_id: str,
    body,
    *,
    actor_user_id: str,
    messages: MessageRepository,
    users: UserRepository,
) -> MessageRead:
    sender = await users.get(actor_user_id)
    if sender is None:
        raise RuntimeError("Пользователь не найден.")
    message_id = uuid4().hex
    sent_at = datetime.now(tz=UTC)
    await messages.create_message(
        message_id=message_id,
        channel_id=channel_id,
        thread_id=body.thread_id,
        parent_message_id=body.parent_message_id,
        sender_user_id=actor_user_id,
        status=MessageStatus.SENT.value,
        sent_at=sent_at,
        contents=body.contents,
    )
    return MessageRead(
        id=message_id,
        channel_id=channel_id,
        thread_id=body.thread_id,
        parent_message_id=body.parent_message_id,
        sender=UserBrief(id=sender.id, display_name=sender.display_name, avatar_url=sender.avatar_url),
        status=MessageStatus.SENT,
        sent_at=sent_at,
        edited_at=None,
        contents=body.contents,
    )


async def _create_thread(
    body,
    *,
    actor_user_id: str,
    threads: ThreadRepository,
    messages: MessageRepository,
    users: UserRepository,
) -> ThreadRead:
    root = await messages.get(body.root_message_id)
    if root is None:
        raise ValueError("root_message_id не найден.")
    creator = await users.get(actor_user_id)
    if creator is None:
        raise RuntimeError("Пользователь не найден.")
    thread_id = uuid4().hex
    row = ThreadRow(
        id=thread_id,
        channel_id=root.channel_id,
        root_message_id=body.root_message_id,
        title=body.title,
        created_at=datetime.now(tz=UTC),
        created_by_user_id=actor_user_id,
    )
    await threads.set(row)
    return ThreadRead(
        id=row.id,
        channel_id=row.channel_id,
        root_message_id=row.root_message_id,
        title=row.title,
        created_at=row.created_at,
        created_by=UserBrief(id=creator.id, display_name=creator.display_name, avatar_url=creator.avatar_url),
    )


async def _upsert_git_resource(body, *, git_refs: GitResourceRefRepository) -> GitResourceRefRead:
    ref_id = f"{body.provider.value}:{body.kind.value}:{body.project_key}:{body.external_id}"
    ref = GitResourceRefRead(
        id=ref_id,
        provider=body.provider,
        kind=body.kind,
        project_key=body.project_key,
        external_id=body.external_id,
        url=body.url,
        extra=body.extra or {},
    )
    await git_refs.set(ref)
    return ref
