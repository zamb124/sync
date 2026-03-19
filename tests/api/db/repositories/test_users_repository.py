from __future__ import annotations

import pytest

from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.models.users import UserRead
from core.db import Database


@pytest.mark.asyncio
async def test_user_repository_all_methods(database: Database, db_clean: None) -> None:
    repo = UserRepository(database)

    user_1 = UserRead(
        id="user_1",
        display_name="User One",
        avatar_url=None,
        email="user1@example.com",
        username="user1",
        first_name="User",
        last_name="One",
        is_active=True,
        external_id=None,
    )
    user_2 = UserRead(
        id="user_2",
        display_name="User Two",
        avatar_url="https://example.com/a.png",
        email="user2@example.com",
        username="user2",
        first_name="User",
        last_name="Two",
        is_active=False,
        external_id="ext-2",
    )

    await repo.set(user_1)
    await repo.set(user_2)

    got = await repo.get("user_1")
    assert got is not None
    assert got.email == "user1@example.com"

    by_email = await repo.get_by_email("user2@example.com")
    assert by_email is not None
    assert by_email.id == "user_2"

    by_username = await repo.get_by_username("user1")
    assert by_username is not None
    assert by_username.id == "user_1"

    active = await repo.list_active(limit=10, offset=0)
    assert [u.id for u in active] == ["user_1"]

    listed = await repo.list(limit=10, offset=0)
    assert {u.id for u in listed} == {"user_1", "user_2"}

    await repo.delete("user_2")
    assert await repo.get("user_2") is None

