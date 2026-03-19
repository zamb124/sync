"""Менеджер поднятия chat_worker (TaskIQ worker) в тестах."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ChatWorker:
    """Запущенный chat_worker процесс."""

    pid: int


class ChatWorkerManager:
    def __init__(self, *, env: Mapping[str, str]) -> None:
        self._env = dict(env)
        self._process: subprocess.Popen[str] | None = None

    def start(self) -> ChatWorker:
        if self._process is not None:
            raise RuntimeError("ChatWorkerManager уже запущен.")

        self._process = subprocess.Popen(  # noqa: S603
            [
                "uv",
                "run",
                "taskiq",
                "worker",
                "apps.api.src.realtime.broker:broker",
                "apps.api.src.realtime.tasks",
            ],
            env=self._env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self._wait_ready(timeout_s=20.0)
        return ChatWorker(pid=int(self._process.pid))

    def _wait_ready(self, *, timeout_s: float) -> None:
        """Проверяет, что worker реально исполняет TaskIQ задачи.

        Важно: проверка выполняется в отдельном `uv run python`, чтобы настройки
        TaskIQ читались из env фикстур (а не из import-time состояния pytest).
        """

        code = (
            "import asyncio\n"
            "import time\n"
            "from taskiq.exceptions import TaskiqResultTimeoutError\n"
            "from apps.api.src.realtime.tasks import handle_command\n"
            "\n"
            "async def main() -> None:\n"
            "  deadline = time.time() + 20.0\n"
            "  last = None\n"
            "  while time.time() < deadline:\n"
            "    task = await handle_command.kiq({\n"
            "      'id': f'health-check:{time.time()}',\n"
            "      'actor_user_id': 'test-user',\n"
            "      'type': 'spaces.create',\n"
            "      'payload': {'body': {'name': 'health-space', 'description': None}},\n"
            "    })\n"
            "    try:\n"
            "      res = await task.wait_result(timeout=1.0)\n"
            "    except TaskiqResultTimeoutError as exc:\n"
            "      last = exc\n"
            "      continue\n"
            "    if res.is_err:\n"
            "      last = res.error\n"
            "      continue\n"
            "    if res.return_value.get('ok') is True:\n"
            "      return\n"
            "    last = res.return_value\n"
            "  raise RuntimeError(f'chat_worker не готов: {last}')\n"
            "\n"
            "asyncio.run(main())\n"
        )
        subprocess.run(  # noqa: S603
            ["uv", "run", "python", "-c", code],
            check=True,
            env=self._env,
            timeout=timeout_s,
        )

    def stop(self) -> None:
        if self._process is None:
            return

        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
        finally:
            self._process = None

