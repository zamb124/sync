"""Точка входа FastAPI-сервиса API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket

from apps.api.api import get_api_router
from apps.api.container import build_container, set_container as set_api_container
from apps.api.config import ApiSettings
from apps.api.ws import fanout, websocket_endpoint
from core.auth import JwtAuthMiddleware
from core.config import set_settings as set_core_settings
from core.db import Database


settings = ApiSettings()
static_dist_dir = Path(__file__).parent / "static" / "dist"
static_assets_dir = static_dist_dir / "assets"
static_index_html = static_dist_dir / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not static_index_html.is_file():
        raise RuntimeError(
            "Фронтенд не собран: не найден apps/api/static/dist/index.html. "
            "Соберите UI (vite build) перед запуском сервиса."
        )

    set_core_settings(settings)

    container = build_container(settings)
    set_api_container(container)
    app.state.container = container

    database = container.resolve(Database)
    await database.connect()
    app.state.database = database
    await fanout.start()
    try:
        yield
    finally:
        await fanout.stop()
        await database.close()


app = FastAPI(
    title="Sync API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    JwtAuthMiddleware,
    jwt_secret=settings.auth.jwt_secret,
    jwt_algorithm=settings.auth.jwt_algorithm,
    public_paths={"/", "/auth", "/api/health", "/api/ready", "/api/auth/login", "/api/auth/register"},
    public_path_prefixes={"/assets/"},
)

app.mount("/assets", StaticFiles(directory=str(static_assets_dir)), name="assets")


@app.get("/")
async def public_root() -> FileResponse:
    return FileResponse(static_index_html)


@app.get("/auth")
async def auth_page() -> FileResponse:
    return FileResponse(static_index_html)


@app.get("/chat")
async def chat_page() -> FileResponse:
    return FileResponse(static_index_html)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket_endpoint(websocket)

app.include_router(get_api_router(), prefix="/api")


