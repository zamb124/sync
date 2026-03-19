"""Репозиторий для работы с каналами."""

from apps.api.src.models.channels import ChannelRead
from core.db.base_sql_repository import CoreRepository


class ChannelRepository(CoreRepository[ChannelRead]):
    """Репозиторий для работы с каналами."""
    
    model_class = ChannelRead

    def _table_name(self) -> str:
        return "channels"
    
    # Наследует базовую реализацию _from_row и _to_row из CoreRepository
    # Переопределяем только при необходимости специальной логики преобразования
    
    async def list_by_space(self, space_id: str, limit: int, offset: int) -> list[ChannelRead]:
        query = """SELECT * FROM channels WHERE space_id = $1 ORDER BY name ASC LIMIT $2 OFFSET $3"""
        rows = await self.fetch(query, space_id, limit, offset)
        return [self._from_row(row) for row in rows]
    
    async def is_member(self, channel_id: str, user_id: str) -> bool:
        query = """SELECT EXISTS(SELECT 1 FROM channel_members WHERE channel_id = $1 AND user_id = $2)"""
        return bool(await self.fetchval(query, channel_id, user_id))

    async def upsert_member(self, channel_id: str, user_id: str, role: str) -> None:
        query = """
        INSERT INTO channel_members (channel_id, user_id, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (channel_id, user_id) DO UPDATE SET role = EXCLUDED.role
        """
        await self.execute(query, channel_id, user_id, role)

    async def add_member_if_missing(self, channel_id: str, user_id: str, role: str) -> None:
        query = """
        INSERT INTO channel_members (channel_id, user_id, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (channel_id, user_id) DO NOTHING
        """
        await self.execute(query, channel_id, user_id, role)