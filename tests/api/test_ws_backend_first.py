from __future__ import annotations

import asyncio
import json
import uuid
from urllib.request import Request, urlopen

import pytest
import websockets

from tests.fixtures.api_server_manager import ApiServer
from tests.fixtures.auth_fixture import UserAuth


def _post_json(url: str, payload: dict, *, headers: dict[str, str] | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, method="POST", data=body, headers={"Content-Type": "application/json", **(headers or {})})
    with urlopen(req, timeout=5.0) as resp:  # nosec - тестовая среда
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, *, headers: dict[str, str] | None = None) -> dict:
    req = Request(url, method="GET", headers=headers or {})
    with urlopen(req, timeout=5.0) as resp:  # nosec - тестовая среда
        return json.loads(resp.read().decode("utf-8"))


def _login(base_url: str, *, username: str, password: str) -> str:
    res = _post_json(f"{base_url}/api/auth/login", {"login": username, "password": password})
    token = res.get("access_token")
    if not isinstance(token, str) or token.strip() == "":
        raise RuntimeError("login не вернул access_token.")
    return token


def test_ws_command_send_message_returns_result(api_server: ApiServer, user_auth: UserAuth) -> None:
    base_url = api_server.base_url
    token = user_auth.jwt

    space = _post_json(
        f"{base_url}/api/spaces/",
        {"name": "ws-space", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    space_id = space["id"]

    channel = _post_json(
        f"{base_url}/api/channels/",
        {"space_id": space_id, "type": "topic", "name": "ws-test", "is_private": False, "member_ids": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    channel_id = channel["id"]

    ws_url = base_url.replace("http://", "ws://") + f"/ws?token={token}"

    async def _run() -> None:
        async with websockets.connect(ws_url, open_timeout=5.0, close_timeout=2.0) as ws:
            cmd_id = str(uuid.uuid4())
            await ws.send(
                json.dumps(
                    {
                        "id": cmd_id,
                        "type": "messages.send",
                        "payload": {
                            "channel_id": channel_id,
                            "body": {
                                "thread_id": None,
                                "parent_message_id": None,
                                "contents": [{"type": "text/plain", "data": {"body": "hello"}, "order": 0}],
                            },
                        },
                    },
                    ensure_ascii=False,
                )
            )
            deadline_s = asyncio.get_running_loop().time() + 5.0
            while asyncio.get_running_loop().time() < deadline_s:
                raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("id") == cmd_id:
                    assert data["ok"] is True
                    assert data["result"]["channel_id"] == channel_id
                    return
            raise AssertionError("Не получили WsResultFrame для команды.")

    asyncio.run(_run())


def test_ws_command_create_thread_and_git_resource(api_server: ApiServer, user_auth: UserAuth) -> None:
    base_url = api_server.base_url
    token = user_auth.jwt

    space = _post_json(
        f"{base_url}/api/spaces/",
        {"name": "parity-space", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    channel = _post_json(
        f"{base_url}/api/channels/",
        {"space_id": space["id"], "type": "topic", "name": "parity-channel", "is_private": False, "member_ids": None},
        headers={"Authorization": f"Bearer {token}"},
    )

    msg = _post_json(
        f"{base_url}/api/channels/{channel['id']}/messages",
        {"thread_id": None, "parent_message_id": None, "contents": [{"type": "text/plain", "data": {"body": "root"}, "order": 0}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    # REST: thread.create
    thread_rest = _post_json(
        f"{base_url}/api/threads/",
        {"root_message_id": msg["id"], "title": "t"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert thread_rest["root_message_id"] == msg["id"]

    # REST: git.resources.upsert
    git_rest = _post_json(
        f"{base_url}/api/git/resources",
        {
            "provider": "gitlab",
            "kind": "merge_request",
            "project_key": "group/proj",
            "external_id": "123",
            "url": "https://gitlab.example.com/group/proj/-/merge_requests/123",
            "extra": {"k": "v"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert git_rest["provider"] == "gitlab"

    ws_url = base_url.replace("http://", "ws://") + f"/ws?token={token}"

    async def _run() -> None:
        async with websockets.connect(ws_url, open_timeout=5.0, close_timeout=2.0) as ws:
            cmd_thread = str(uuid.uuid4())
            await ws.send(
                json.dumps(
                    {"id": cmd_thread, "type": "threads.create", "payload": {"body": {"root_message_id": msg["id"], "title": "t2"}}},
                    ensure_ascii=False,
                )
            )
            cmd_git = str(uuid.uuid4())
            await ws.send(
                json.dumps(
                    {
                        "id": cmd_git,
                        "type": "git.resources.upsert",
                        "payload": {
                            "body": {
                                "provider": "gitlab",
                                "kind": "merge_request",
                                "project_key": "group/proj",
                                "external_id": "124",
                                "url": "https://gitlab.example.com/group/proj/-/merge_requests/124",
                                "extra": None,
                            }
                        },
                    },
                    ensure_ascii=False,
                )
            )

            got_thread = False
            got_git = False
            deadline_s = asyncio.get_running_loop().time() + 8.0
            while asyncio.get_running_loop().time() < deadline_s and (not got_thread or not got_git):
                raw = await asyncio.wait_for(ws.recv(), timeout=8.0)
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("id") == cmd_thread:
                    assert data["ok"] is True
                    assert data["result"]["root_message_id"] == msg["id"]
                    got_thread = True
                if isinstance(data, dict) and data.get("id") == cmd_git:
                    assert data["ok"] is True
                    assert data["result"]["external_id"] == "124"
                    got_git = True
            assert got_thread is True
            assert got_git is True

    asyncio.run(_run())

