"""Точка входа FastAPI-сервиса API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.api import get_api_router
from apps.api.config import ApiSettings
from core.db import Database


settings = ApiSettings()
database = Database(dsn=settings.database.url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    app.state.database = database
    try:
        yield
    finally:
        await database.close()


app = FastAPI(
    title="Sync API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(get_api_router(), prefix="/api")


