"""Репозиторий для работы с Git-ресурсами."""

from __future__ import annotations

from apps.api.src.models.git import GitResourceRefRead
from core.db.base_sql_repository import CoreRepository


class GitResourceRefRepository(CoreRepository[GitResourceRefRead]):
    """Репозиторий для работы с git_resource_refs."""

    model_class = GitResourceRefRead

    def _table_name(self) -> str:
        return "git_resource_refs"

