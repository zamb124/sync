"""Менеджер тестовой инфраструктуры (PostgreSQL + Redis) для интеграционных тестов."""

from __future__ import annotations

import asyncio
import os
import subprocess
import time
from dataclasses import dataclass

import asyncpg
import redis.asyncio as redis


async def _wait_postgres_ready(dsn: str, *, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    last: Exception | None = None
    while time.time() < deadline:
        try:
            conn = await asyncpg.connect(dsn)
            try:
                await conn.fetchval("select 1")
                return
            finally:
                await conn.close()
        except Exception as exc:
            last = exc
            await asyncio.sleep(0.5)
    raise RuntimeError(f"PostgreSQL не готов за {timeout_s:.1f}s: {last}")


async def _assert_schema_ready(dsn: str) -> None:
    conn = await asyncpg.connect(dsn)
    try:
        val = await conn.fetchval("select to_regclass('public.spaces')")
        if val != "spaces":
            raise RuntimeError("Миграции не применились: таблица spaces отсутствует.")
    finally:
        await conn.close()


async def _wait_redis_ready(dsn: str, *, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    last: Exception | None = None
    while time.time() < deadline:
        try:
            r = redis.from_url(dsn)
            try:
                pong = await r.ping()
                if pong is True:
                    return
            finally:
                await r.aclose()
        except Exception as exc:
            last = exc
            await asyncio.sleep(0.2)
    raise RuntimeError(f"Redis не готов за {timeout_s:.1f}s: {last}")


@dataclass(frozen=True)
class InfraRuntime:
    postgres_dsn: str
    redis_dsn: str


class InfraManager:
    def __init__(self, *, env: dict[str, str]) -> None:
        self._env = dict(env)
        self._started = False

    def start(self, *, timeout_s: float = 60.0) -> InfraRuntime:
        if self._started:
            raise RuntimeError("TestInfraManager уже запущен.")

        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            check=True,
            env=self._env,
        )

        postgres_dsn = self._env["API__DATABASE__URL"]
        asyncio.run(_wait_postgres_ready(postgres_dsn, timeout_s=timeout_s))
        redis_dsn = self._env["API__DATABASE__REDIS_URL"]
        asyncio.run(_wait_redis_ready(redis_dsn, timeout_s=timeout_s))

        subprocess.run(
            ["uv", "run", "alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"],
            check=True,
            env=self._env,
        )
        asyncio.run(_assert_schema_ready(postgres_dsn))

        self._started = True
        return InfraRuntime(
            postgres_dsn=postgres_dsn,
            redis_dsn=redis_dsn,
        )

    def stop(self) -> None:
        if not self._started:
            return

        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
            check=True,
            env=self._env,
        )
        self._started = False

