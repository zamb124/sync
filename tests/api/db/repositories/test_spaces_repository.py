from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.src.db.repositories.spaces import SpaceRepository
from apps.api.src.models.spaces import SpaceRead
from core.db import Database


@pytest.mark.asyncio
async def test_space_repository_all_methods(database: Database, db_clean: None) -> None:
    repo = SpaceRepository(database)

    space_1 = SpaceRead(
        id="space_1",
        name="Space One",
        description="desc",
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_1",
    )
    space_2 = SpaceRead(
        id="space_2",
        name="Space Two",
        description=None,
        created_at=datetime.now(tz=UTC),
        created_by_user_id="user_2",
    )

    await repo.set(space_1)
    await repo.set(space_2)

    got = await repo.get("space_1")
    assert got is not None
    assert got.id == "space_1"
    assert got.name == "Space One"

    by_name = await repo.get_by_name("Space Two")
    assert by_name is not None
    assert by_name.id == "space_2"

    by_user = await repo.list_by_user("user_1", limit=10, offset=0)
    assert [s.id for s in by_user] == ["space_1"]

    listed = await repo.list(limit=10, offset=0)
    assert {s.id for s in listed} == {"space_1", "space_2"}

    await repo.delete("space_2")
    assert await repo.get("space_2") is None

