"""Модели аутентификации для проекта sync."""

from __future__ import annotations

from dataclasses import dataclass

from core.auth.jwt import JwtClaims


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    claims: JwtClaims

