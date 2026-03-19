"""Репозиторий для работы с пользователями."""

from apps.api.src.models.users import UserRead
from core.db.base_sql_repository import CoreRepository


class UserRepository(CoreRepository[UserRead]):
    """Репозиторий для работы с пользователями."""
    
    model_class = UserRead

    def _table_name(self) -> str:
        return "users"
    
    # Наследует базовую реализацию _from_row и _to_row из CoreRepository
    # Переопределяем только при необходимости специальной логики преобразования
    
    async def get_by_email(self, email: str) -> UserRead | None:
        query = """SELECT * FROM users WHERE email = $1"""
        row = await self.fetchrow(query, email)
        return self._from_row(row) if row else None
    
    async def get_by_username(self, username: str) -> UserRead | None:
        query = """SELECT * FROM users WHERE username = $1"""
        row = await self.fetchrow(query, username)
        return self._from_row(row) if row else None

    async def get_password_hash(self, user_id: str) -> str | None:
        query = """SELECT password_hash FROM users WHERE id = $1"""
        row = await self.fetchrow(query, user_id)
        if row is None:
            return None
        password_hash = row.get("password_hash")
        if password_hash is None:
            return None
        if not isinstance(password_hash, str):
            raise RuntimeError("Некорректный тип users.password_hash в БД.")
        return password_hash
    
    async def list_active(self, limit: int, offset: int) -> list[UserRead]:
        query = """SELECT * FROM users WHERE is_active = true ORDER BY last_name, first_name LIMIT $1 OFFSET $2"""
        rows = await self.fetch(query, limit, offset)
        return [self._from_row(row) for row in rows]

    async def create_user(
        self,
        *,
        user_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        display_name: str,
        password_hash: str,
    ) -> None:
        query = """
        INSERT INTO users (id, email, username, first_name, last_name, display_name, password_hash, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, true)
        """
        await self.execute(
            query,
            user_id,
            email,
            username,
            first_name,
            last_name,
            display_name,
            password_hash,
        )