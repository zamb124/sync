"""Репозиторий для работы с пространствами."""

from apps.api.src.models.spaces import SpaceRead
from core.db.base_sql_repository import CoreRepository


class SpaceRepository(CoreRepository[SpaceRead]):
    """Репозиторий для работы с пространствами."""
    
    model_class = SpaceRead

    def _table_name(self) -> str:
        return "spaces"
    
    # Наследует базовую реализацию _from_row и _to_row из CoreRepository
    # Переопределяем только при необходимости специальной логики преобразования
    
    async def get_by_name(self, name: str) -> SpaceRead | None:
        query = """SELECT * FROM spaces WHERE name = $1"""
        row = await self.fetchrow(query, name)
        return self._from_row(row) if row else None
    
    async def list_by_user(self, user_id: str, limit: int, offset: int) -> list[SpaceRead]:
        query = """SELECT * FROM spaces WHERE created_by_user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3"""
        rows = await self.fetch(query, user_id, limit, offset)
        return [self._from_row(row) for row in rows]