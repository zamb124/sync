from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.src.db.repositories.threads import ThreadRepository
from apps.api.src.models.threads import ThreadRow
from core.db import Database


@pytest.mark.asyncio
async def test_thread_repository_all_methods(database: Database, db_clean: None) -> None:
    repo = ThreadRepository(database)

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

    thread_1 = ThreadRow(
        id="thread_1",
        channel_id="channel_1",
        root_message_id="msg_root_1",
        title="t1",
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_1",
    )
    thread_2 = ThreadRow(
        id="thread_2",
        channel_id="channel_1",
        root_message_id="msg_root_2",
        title=None,
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_1",
    )

    await repo.set(thread_1)
    await repo.set(thread_2)

    got = await repo.get("thread_1")
    assert got is not None
    assert got.root_message_id == "msg_root_1"

    by_channel = await repo.list_by_channel("channel_1", limit=10, offset=0)
    assert {t.id for t in by_channel} == {"thread_1", "thread_2"}

    listed = await repo.list(limit=10, offset=0)
    assert {t.id for t in listed} == {"thread_1", "thread_2"}

    await repo.delete("thread_2")
    assert await repo.get("thread_2") is None

