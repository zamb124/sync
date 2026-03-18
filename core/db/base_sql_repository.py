"""Базовый SQL‑репозиторий, работающий через Database."""

from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar

import asyncpg

from core.db import Database


class BaseSQLRepository:
    """Общий базовый класс для репозиториев, использующих PostgreSQL.

    Содержит общие низкоуровневые методы работы с SQL. Репозитории сущностей
    наследуются от этого класса и реализуют только доменно-специфичные методы.
    """

    def __init__(self, database: Database) -> None:
        self._database = database

    @property
    def database(self) -> Database:
        return self._database

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        return await self._database.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        return await self._database.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self._database.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        return await self._database.execute(query, *args)

    async def fetch_one(self, query: str, *args: Any) -> asyncpg.Record:
        row = await self.fetchrow(query, *args)
        if row is None:
            raise ValueError("Ожидалась как минимум одна строка, но запрос вернул пустой результат.")
        return row

    async def fetch_optional(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        return await self.fetchrow(query, *args)

    async def fetch_many(self, query: str, *args: Any) -> list[asyncpg.Record]:
        return await self.fetch(query, *args)

    async def execute_many(self, query: str, args_seq: Sequence[Sequence[Any]]) -> None:
        for args in args_seq:
            await self.execute(query, *args)


T = TypeVar("T")


class CoreRepository(BaseSQLRepository, Generic[T]):
    """Базовый репозиторий сущности с единым интерфейсом get/set/list/delete."""

    def __init__(self, database: Database) -> None:
        super().__init__(database)

    def _table_name(self) -> str:
        raise NotImplementedError("Метод _table_name() должен быть реализован в наследнике.")

    def _pk_column(self) -> str:
        return "id"

    def _from_row(self, row: asyncpg.Record) -> T:
        raise NotImplementedError("Метод _from_row() должен быть реализован в наследнике.")

    def _to_row(self, entity: T) -> dict[str, Any]:
        raise NotImplementedError("Метод _to_row() должен быть реализован в наследнике.")

    async def get(self, entity_id: str) -> Optional[T]:
        query = f"""
        SELECT *
        FROM {self._table_name()}
        WHERE {self._pk_column()} = $1
        """
        row = await self.fetchrow(query, entity_id)
        if row is None:
            return None
        return self._from_row(row)

    async def delete(self, entity_id: str) -> None:
        query = f"""
        DELETE FROM {self._table_name()}
        WHERE {self._pk_column()} = $1
        """
        await self.execute(query, entity_id)

    async def list(self, limit: int, offset: int) -> list[T]:
        query = f"""
        SELECT *
        FROM {self._table_name()}
        ORDER BY {self._pk_column()}
        LIMIT $1 OFFSET $2
        """
        rows = await self.fetch(query, limit, offset)
        return [self._from_row(row) for row in rows]

    async def set(self, entity: T) -> T:
        data = self._to_row(entity)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i}" for i in range(1, len(data) + 1))
        pk = self._pk_column()
        update_set_parts = [f"{col} = EXCLUDED.{col}" for col in data.keys() if col != pk]
        update_set = ", ".join(update_set_parts)

        query = f"""
        INSERT INTO {self._table_name()} ({columns})
        VALUES ({placeholders})
        ON CONFLICT ({pk}) DO UPDATE
        SET {update_set}
        """
        await self.execute(query, *data.values())
        return entity


