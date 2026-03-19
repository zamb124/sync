from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.src.db.repositories.channels import ChannelRepository
from apps.api.src.models.channels import ChannelRead, ChannelType
from core.db import Database


@pytest.mark.asyncio
async def test_channel_repository_all_methods(database: Database, db_clean: None) -> None:
    repo = ChannelRepository(database)

    await database.execute(
        """
        INSERT INTO spaces (id, name, description, created_at, created_by_user_id)
        VALUES ($1, $2, $3, $4, $5)
        """,
        "space_1",
        "Space One",
        None,
        datetime.now(tz=UTC),
        "user_1",
    )

    channel_1 = ChannelRead(
        id="channel_1",
        space_id="space_1",
        type=ChannelType.TOPIC,
        name="general",
        is_private=False,
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_1",
    )
    channel_2 = ChannelRead(
        id="channel_2",
        space_id="space_1",
        type=ChannelType.GROUP,
        name="backend",
        is_private=True,
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_1",
    )

    await repo.set(channel_1)
    await repo.set(channel_2)

    got = await repo.get("channel_1")
    assert got is not None
    assert got.name == "general"

    listed = await repo.list(limit=10, offset=0)
    assert {c.id for c in listed} == {"channel_1", "channel_2"}

    by_space = await repo.list_by_space("space_1", limit=10, offset=0)
    assert [c.id for c in by_space] == ["channel_2", "channel_1"]

    await database.execute(
        "INSERT INTO channel_members (channel_id, user_id, role) VALUES ($1, $2, $3)",
        "channel_1",
        "user_10",
        "member",
    )
    assert await repo.is_member("channel_1", "user_10") is True
    assert await repo.is_member("channel_1", "user_11") is False

    await repo.delete("channel_2")
    assert await repo.get("channel_2") is None

