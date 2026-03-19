"""Роутеры авторизации."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.db.repositories.users import UserRepository
from apps.api.src.models.auth import LoginRequest, LoginResponse, RegisterRequest
from apps.api.src.models.users import UserRead
from core.auth.jwt import encode_hs256
from core.auth.passwords import hash_password, verify_password
from core.config import settings


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    repo: UserRepository = Depends(UserRepository),
) -> LoginResponse:
    user = await _get_user_by_login(repo, payload.login)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")

    password_hash = await repo.get_password_hash(user.id)
    if password_hash is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=401, detail="Unauthorized")

    exp_minutes = settings.auth.access_token_expire_minutes
    if exp_minutes <= 0:
        raise RuntimeError("auth.access_token_expire_minutes должен быть > 0.")
    exp_dt = datetime.now(tz=UTC) + timedelta(minutes=exp_minutes)
    claims = {"sub": user.id, "exp": exp_dt.timestamp()}
    token = encode_hs256(claims, secret=settings.auth.jwt_secret)
    return LoginResponse(access_token=token)


@router.post("/register", response_model=LoginResponse)
async def register(
    payload: RegisterRequest,
    repo: UserRepository = Depends(UserRepository),
) -> LoginResponse:
    existing_email = await repo.get_by_email(payload.email)
    if existing_email is not None:
        raise HTTPException(status_code=409, detail="Email already exists.")
    existing_username = await repo.get_by_username(payload.username)
    if existing_username is not None:
        raise HTTPException(status_code=409, detail="Username already exists.")

    user_id = uuid4().hex
    password_hash = hash_password(payload.password)
    await repo.create_user(
        user_id=user_id,
        email=payload.email,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        display_name=payload.display_name,
        password_hash=password_hash,
    )

    exp_minutes = settings.auth.access_token_expire_minutes
    if exp_minutes <= 0:
        raise RuntimeError("auth.access_token_expire_minutes должен быть > 0.")
    exp_dt = datetime.now(tz=UTC) + timedelta(minutes=exp_minutes)
    claims = {"sub": user_id, "exp": exp_dt.timestamp()}
    token = encode_hs256(claims, secret=settings.auth.jwt_secret)
    return LoginResponse(access_token=token)


async def _get_user_by_login(repo: UserRepository, login: str) -> UserRead | None:
    if login == "":
        raise ValueError("login не должен быть пустым.")
    if "@" in login:
        return await repo.get_by_email(login)
    return await repo.get_by_username(login)

