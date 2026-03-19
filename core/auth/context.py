"""Контекст текущего запроса (request scope) для auth.

Нужен, чтобы в любом месте кода можно было получить текущего пользователя
без прокидывания его через десятки слоёв.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

from core.auth.models import AuthenticatedUser


_current_user: ContextVar[AuthenticatedUser | None] = ContextVar("sync_current_user", default=None)


def set_current_user(user: AuthenticatedUser | None) -> Token[AuthenticatedUser | None]:
    if user is not None and not isinstance(user, AuthenticatedUser):
        raise RuntimeError("Некорректный тип user для контекста.")
    token = _current_user.set(user)
    return token


def reset_current_user(token: Token[AuthenticatedUser | None]) -> None:
    _current_user.reset(token)


def current_user() -> AuthenticatedUser | None:
    return _current_user.get()


def require_user() -> AuthenticatedUser:
    user = _current_user.get()
    if user is None:
        raise RuntimeError("Пользователь не установлен в контексте запроса.")
    return user

