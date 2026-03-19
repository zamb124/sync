from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class UserAuth:
    user_id_hint: str
    username: str
    password: str
    jwt: str


def _post_json(url: str, payload: dict, *, headers: dict[str, str] | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, method="POST", data=body, headers={"Content-Type": "application/json", **(headers or {})})
    with urlopen(req, timeout=5.0) as resp:  # nosec - тестовая среда
        return json.loads(resp.read().decode("utf-8"))


def create_user_and_jwt(*, base_url: str) -> UserAuth:
    username = f"u_{uuid.uuid4().hex[:10]}"
    password = "test-password"

    _post_json(
        f"{base_url}/api/auth/register",
        {
            "email": f"{username}@example.com",
            "username": username,
            "first_name": "Test",
            "last_name": "User",
            "display_name": "Test User",
            "password": password,
        },
    )
    login = _post_json(f"{base_url}/api/auth/login", {"login": username, "password": password})
    token = login.get("access_token")
    if not isinstance(token, str) or token.strip() == "":
        raise RuntimeError("login не вернул access_token.")
    return UserAuth(user_id_hint="", username=username, password=password, jwt=token)

