from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.models.messages import MessageContentRow, MessageRow
from core.db import Database


@pytest.mark.asyncio
async def test_message_repository_all_methods(database: Database, db_clean: None) -> None:
    repo = MessageRepository(database)

    await database.execute(
        """
        INSERT INTO channels (id, space_id, type, name, is_private, created_at, created_by_user_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        "channel_1",
        None,
        "topic",
        "general",
        False,
        datetime.now(tz=UTC),
        "user_1",
    )
    await database.execute(
        """
        INSERT INTO threads (id, channel_id, root_message_id, title, created_at, created_by_user_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        "thread_1",
        "channel_1",
        "msg_root",
        None,
        datetime.now(tz=UTC),
        "user_1",
    )

    root = MessageRow(
        id="msg_root",
        channel_id="channel_1",
        thread_id="thread_1",
        parent_message_id=None,
        sender_user_id="user_1",
        status="sent",
        sent_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        edited_at=None,
    )
    reply = MessageRow(
        id="msg_reply",
        channel_id="channel_1",
        thread_id="thread_1",
        parent_message_id="msg_root",
        sender_user_id="user_2",
        status="sent",
        sent_at=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
        edited_at=None,
    )
    other_root = MessageRow(
        id="msg_other_root",
        channel_id="channel_1",
        thread_id=None,
        parent_message_id=None,
        sender_user_id="user_3",
        status="sent",
        sent_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
        edited_at=None,
    )

    await repo.set(root)
    await repo.set(reply)
    await repo.set(other_root)

    got = await repo.get("msg_root")
    assert got is not None
    assert got.id == "msg_root"

    listed_channel = await repo.list_by_channel("channel_1", limit=10, offset=0)
    assert [m.id for m in listed_channel] == ["msg_root", "msg_other_root"]

    listed_thread = await repo.list_by_thread("thread_1", limit=10, offset=0)
    assert [m.id for m in listed_thread] == ["msg_root", "msg_reply"]

    thread_root = await repo.get_thread_root("msg_reply")
    assert thread_root is not None
    assert thread_root.id == "msg_root"

    await database.execute(
        """
        INSERT INTO message_contents (message_id, type, "order", data)
        VALUES ($1, $2, $3, $4), ($1, $5, $6, $7)
        """,
        "msg_root",
        "text/plain",
        1,
        {"body": "hello"},
        "code/block",
        2,
        {"language": "python", "source": "print(1)"},
    )
    contents = await repo.list_contents("msg_root")
    assert [c.type for c in contents] == ["text/plain", "code/block"]
    assert contents[0].data["body"] == "hello"

    listed_all = await repo.list(limit=10, offset=0)
    assert {m.id for m in listed_all} == {"msg_root", "msg_reply", "msg_other_root"}

    await repo.delete("msg_reply")
    assert await repo.get("msg_reply") is None

