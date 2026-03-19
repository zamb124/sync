"""Менеджер поднятия API-сервиса в тестах (без моков).

Поднимает реальный HTTP-сервер uvicorn с приложением `apps.api.main:app`.
Используется для интеграционных тестов API по HTTP и для тестов интеграции
других сервисов с API.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Mapping
from urllib.error import URLError
from urllib.request import urlopen


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_ready(base_url: str, *, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    url = f"{base_url}/"
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.0) as resp:  # nosec - тестовая среда
                if int(resp.status) == 200:
                    return
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(0.2)

    raise RuntimeError(f"API не поднялся за {timeout_s:.1f}s. Последняя ошибка: {last_error}")


@dataclass(frozen=True)
class ApiServer:
    """Запущенный API сервер."""

    base_url: str


class ApiServerManager:
    """Запускает/останавливает API сервер для тестов."""

    def __init__(self, *, env: Mapping[str, str]) -> None:
        self._env = dict(env)
        self._process: subprocess.Popen[str] | None = None
        self._port: int | None = None

    def start(self, *, timeout_s: float = 30.0) -> ApiServer:
        if self._process is not None:
            raise RuntimeError("ApiServerManager уже запущен.")

        port = _find_free_port()
        base_url = f"http://127.0.0.1:{port}"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "apps.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ]

        self._process = subprocess.Popen(  # noqa: S603
            cmd,
            env=self._env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._port = port

        try:
            _wait_ready(base_url, timeout_s=timeout_s)
        except Exception as exc:
            stdout, stderr = self._drain_pipes()
            self.stop()
            raise RuntimeError(
                "API не смог подняться. "
                f"base_url={base_url}. "
                f"stdout_tail={stdout!r}. "
                f"stderr_tail={stderr!r}."
            ) from exc

        return ApiServer(base_url=base_url)

    def _drain_pipes(self) -> tuple[str, str]:
        process = self._process
        if process is None:
            return "", ""

        if process.poll() is None:
            return "", ""

        try:
            out, err = process.communicate(timeout=0.2)
        except TimeoutError:
            out = ""
            err = ""

        return out[-4000:], err[-4000:]

    def stop(self) -> None:
        if self._process is None:
            return

        self._process.terminate()
        try:
            self._process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5.0)
        finally:
            self._process = None
            self._port = None

