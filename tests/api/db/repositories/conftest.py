from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from apps.api.config import ApiSettings
from core.db import Database


@pytest.fixture(scope="session")
def api_settings(test_env: None) -> ApiSettings:
    return ApiSettings()


@pytest_asyncio.fixture()
async def database(api_settings: ApiSettings) -> AsyncIterator[Database]:
    db = Database(dsn=api_settings.database.url)
    await db.connect()
    try:
        yield db
    finally:
        await db.close()


@pytest_asyncio.fixture()
async def db_clean(database: Database) -> None:
    await database.execute(
        """
        TRUNCATE TABLE
            message_files,
            message_contents,
            messages,
            git_resource_refs,
            files,
            threads,
            channel_members,
            channels,
            spaces,
            users
        RESTART IDENTITY
        CASCADE
        """
    )

