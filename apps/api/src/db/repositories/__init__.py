"""Репозитории API-сервиса."""

from apps.api.src.db.repositories.channels import ChannelRepository
from apps.api.src.db.repositories.messages import MessageRepository
from apps.api.src.db.repositories.spaces import SpaceRepository
from apps.api.src.db.repositories.threads import ThreadRepository
from apps.api.src.db.repositories.users import UserRepository

__all__ = [
    "SpaceRepository",
    "ChannelRepository",
    "ThreadRepository",
    "MessageRepository",
    "UserRepository",
]