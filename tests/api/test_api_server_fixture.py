from __future__ import annotations

import json
from urllib.request import urlopen

import pytest

from urllib.error import HTTPError

from tests.fixtures.api_server_manager import ApiServer


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=2.0) as resp:  # nosec - тестовая среда
        body = resp.read().decode("utf-8")
        return json.loads(body)


def test_api_server_fixture_health(api_server: ApiServer) -> None:
    data = _get_json(f"{api_server.base_url}/api/health")
    assert data == {"status": "ok"}


def test_health_is_public(api_server: ApiServer) -> None:
    data = _get_json(f"{api_server.base_url}/api/health")
    assert data == {"status": "ok"}


def test_api_requires_jwt_for_protected_endpoint(api_server: ApiServer) -> None:
    try:
        _get_json(f"{api_server.base_url}/api/spaces/")
    except HTTPError as exc:
        assert exc.code == 401
        return
    raise AssertionError("Ожидался 401 без Authorization заголовка.")

