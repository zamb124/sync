"""DTO для авторизации в API Sync."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(description="Email или username пользователя.")
    password: str = Field(description="Пароль пользователя.")


class LoginResponse(BaseModel):
    access_token: str = Field(description="JWT access token.")
    token_type: str = Field(default="bearer", description="Схема токена для Authorization заголовка.")


class RegisterRequest(BaseModel):
    email: str = Field(description="Email пользователя (уникальный).")
    username: str = Field(description="Username пользователя (уникальный).")
    first_name: str = Field(description="Имя пользователя.")
    last_name: str = Field(description="Фамилия пользователя.")
    display_name: str = Field(description="Отображаемое имя.")
    password: str = Field(description="Пароль пользователя.")

