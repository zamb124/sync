"""Общий класс доступа к PostgreSQL для сервисов проекта sync."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Optional

import asyncpg


class Database:
    """Обёртка над asyncpg.Pool для конкретной БД сервиса."""

    def __init__(
        self,
        dsn: str,
        *,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        if not dsn:
            raise ValueError("dsn для Database обязателен.")
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None

    @property
    def dsn(self) -> str:
        return self._dsn

    async def connect(self) -> None:
        if self._pool is not None:
            return

        async def _init_connection(connection: asyncpg.Connection) -> None:
            await connection.set_type_codec(
                "json",
                schema="pg_catalog",
                encoder=lambda value: json.dumps(value),
                decoder=lambda value: json.loads(value),
                format="text",
            )
            await connection.set_type_codec(
                "jsonb",
                schema="pg_catalog",
                encoder=lambda value: json.dumps(value),
                decoder=lambda value: json.loads(value),
                format="text",
            )

        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
                init=_init_connection,
            )
        except Exception as exc:
            raise RuntimeError(f"Не удалось создать пул подключений к БД: {exc}") from exc

    async def close(self) -> None:
        if self._pool is None:
            return
        await self._pool.close()
        self._pool = None

    def _ensure_connected(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Пул подключений к БД не инициализирован. Вызовите connect() при старте сервиса.")
        return self._pool

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        pool = self._ensure_connected()
        async with pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        pool = self._ensure_connected()
        async with pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        pool = self._ensure_connected()
        async with pool.acquire() as connection:
            return await connection.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        pool = self._ensure_connected()
        async with pool.acquire() as connection:
            return await connection.execute(query, *args)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        pool = self._ensure_connected()
        async with pool.acquire() as connection:
            async with connection.transaction():
                yield connection


