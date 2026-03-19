"""Репозиторий для работы с тредами."""

from apps.api.src.models.threads import ThreadRow
from core.db.base_sql_repository import CoreRepository


class ThreadRepository(CoreRepository[ThreadRow]):
    """Репозиторий для работы с тредами."""
    
    model_class = ThreadRow

    def _table_name(self) -> str:
        return "threads"
    
    # Наследует базовую реализацию _from_row и _to_row из CoreRepository
    # Переопределяем только при необходимости специальной логики преобразования
    
    async def list_by_channel(self, channel_id: str, limit: int, offset: int) -> list[ThreadRow]:
        query = """SELECT * FROM threads WHERE channel_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3"""
        rows = await self.fetch(query, channel_id, limit, offset)
        return [self._from_row(row) for row in rows]