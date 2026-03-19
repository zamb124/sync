"""Репозиторий для работы с сообщениями."""

from __future__ import annotations

from datetime import datetime

from apps.api.src.models.messages import MessageContentModel, MessageContentRow, MessageRow
from core.db.base_sql_repository import CoreRepository


class MessageRepository(CoreRepository[MessageRow]):
    """Репозиторий для работы с сообщениями."""

    model_class = MessageRow

    def _table_name(self) -> str:
        return "messages"

    async def list_by_channel(self, channel_id: str, limit: int, offset: int) -> list[MessageRow]:
        query = """
        SELECT *
        FROM messages
        WHERE channel_id = $1 AND parent_message_id IS NULL
        ORDER BY sent_at DESC
        LIMIT $2 OFFSET $3
        """
        rows = await self.fetch(query, channel_id, limit, offset)
        return [self._from_row(row) for row in rows]

    async def list_by_thread(self, thread_id: str, limit: int, offset: int) -> list[MessageRow]:
        query = """
        SELECT *
        FROM messages
        WHERE thread_id = $1
        ORDER BY sent_at ASC
        LIMIT $2 OFFSET $3
        """
        rows = await self.fetch(query, thread_id, limit, offset)
        return [self._from_row(row) for row in rows]

    async def get_thread_root(self, message_id: str) -> MessageRow | None:
        query = """
        WITH RECURSIVE thread_path AS (
            SELECT id, parent_message_id
            FROM messages
            WHERE id = $1
            UNION ALL
            SELECT m.id, m.parent_message_id
            FROM messages m
            JOIN thread_path tp ON m.id = tp.parent_message_id
        )
        SELECT m.*
        FROM messages m
        JOIN thread_path tp ON m.id = tp.id
        WHERE tp.parent_message_id IS NULL
        LIMIT 1
        """
        row = await self.fetchrow(query, message_id)
        return self._from_row(row) if row else None

    async def list_contents(self, message_id: str) -> list[MessageContentRow]:
        query = """
        SELECT id, message_id, type, "order", data
        FROM message_contents
        WHERE message_id = $1
        ORDER BY "order" ASC, id ASC
        """
        rows = await self.fetch(query, message_id)
        return [MessageContentRow.model_validate(dict(r)) for r in rows]

    async def create_message(
        self,
        *,
        message_id: str,
        channel_id: str,
        thread_id: str | None,
        parent_message_id: str | None,
        sender_user_id: str,
        status: str,
        sent_at: datetime,
        contents: list[MessageContentModel],
    ) -> None:
        insert_message = """
        INSERT INTO messages (
            id,
            channel_id,
            thread_id,
            parent_message_id,
            sender_user_id,
            status,
            sent_at,
            edited_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, NULL)
        """
        await self.execute(
            insert_message,
            message_id,
            channel_id,
            thread_id,
            parent_message_id,
            sender_user_id,
            status,
            sent_at,
        )

        insert_content = """
        INSERT INTO message_contents (message_id, type, "order", data)
        VALUES ($1, $2, $3, $4)
        """
        for content in contents:
            await self.execute(
                insert_content,
                message_id,
                content.type.value,
                content.order,
                content.data.model_dump(),
            )