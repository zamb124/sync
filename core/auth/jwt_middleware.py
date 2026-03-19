"""JWT middleware для всех сервисов sync."""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.responses import RedirectResponse
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.auth.jwt import JwtClaims, decode_and_verify
from core.auth.context import reset_current_user, set_current_user
from core.auth.models import AuthenticatedUser


class JwtAuthMiddleware:
    """ASGI middleware строгой JWT-авторизации.

    Правила:
    - защищает все HTTP эндпоинты, кроме публичного пути `/`;
    - токен берётся только из `Authorization: Bearer <token>`;
    - при ошибке возвращает 401 без деталей реализации.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        jwt_secret: str,
        jwt_algorithm: str,
        public_paths: set[str],
        public_path_prefixes: set[str] | None = None,
    ) -> None:
        if not jwt_secret:
            raise ValueError("jwt_secret обязателен.")
        if not jwt_algorithm:
            raise ValueError("jwt_algorithm обязателен.")
        if not public_paths:
            raise ValueError("public_paths обязателен.")
        self._app = app
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._public_paths = public_paths
        self._public_path_prefixes = tuple(sorted(public_path_prefixes or set()))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        path = scope.get("path")
        if path in self._public_paths or self._is_public_by_prefix(path):
            await self._app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        auth_header = headers.get("authorization")
        if auth_header is None:
            await self._send_unauthorized(send, headers=headers)
            return

        token = _extract_bearer(auth_header)
        if token is None:
            await self._send_unauthorized(send, headers=headers)
            return

        try:
            claims = decode_and_verify(token, secret=self._jwt_secret, algorithm=self._jwt_algorithm)
        except Exception:
            await self._send_unauthorized(send, headers=headers)
            return

        auth_user = AuthenticatedUser(id=claims.sub, claims=claims)
        scope["user"] = auth_user
        ctx_token = set_current_user(auth_user)
        try:
            await self._app(scope, receive, send)
        finally:
            reset_current_user(ctx_token)

    def _is_public_by_prefix(self, path: object) -> bool:
        if not isinstance(path, str) or path == "":
            return False
        for prefix in self._public_path_prefixes:
            if path.startswith(prefix):
                return True
        return False

    async def _send_unauthorized(self, send: Send, *, headers: Headers) -> None:
        if _is_html_navigation(headers):
            response = RedirectResponse(url="/auth", status_code=307)
            await response({"type": "http", "headers": []}, _empty_receive, send)
            return
        response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        await response({"type": "http", "headers": []}, _empty_receive, send)


def _extract_bearer(auth_header: str) -> str | None:
    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0], parts[1]
    if scheme.lower() != "bearer":
        return None
    if token == "":
        return None
    return token


def _is_html_navigation(headers: Headers) -> bool:
    accept = headers.get("accept")
    if accept is not None and "text/html" in accept:
        return True
    fetch_dest = headers.get("sec-fetch-dest")
    if fetch_dest is not None and fetch_dest == "document":
        return True
    return False


async def _empty_receive() -> Message:
    return {"type": "http.request", "body": b"", "more_body": False}

