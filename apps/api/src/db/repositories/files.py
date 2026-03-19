"""Репозиторий для работы с файлами."""

from __future__ import annotations

from apps.api.src.models.files import FileRead
from core.db.base_sql_repository import CoreRepository


class FileRepository(CoreRepository[FileRead]):
    """Репозиторий для работы с файлами."""

    model_class = FileRead

    def _table_name(self) -> str:
        return "files"

