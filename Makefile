SHELL := /bin/bash

PROJECT_NAME := sync
UV := uv
DOCKER_COMPOSE := docker-compose -f docker-compose.dev.yml
DOCKER_COMPOSE_TEST := docker-compose -f docker-compose.test.yml

.PHONY: dev
dev:
	$(DOCKER_COMPOSE) up -d

.PHONY: test-env
test-env:
	$(DOCKER_COMPOSE_TEST) up -d

.PHONY: test-env-down
test-env-down:
	$(DOCKER_COMPOSE_TEST) down -v

.PHONY: test
test:
	$(DOCKER_COMPOSE_TEST) down -v
	$(DOCKER_COMPOSE_TEST) up -d
	API__DATABASE__URL=postgresql://sync_user:sync_admin@localhost:55432/sync_test_db \
	$(UV) run python -c $$'import asyncio\nimport os\n\nimport asyncpg\n\n\nasync def main() -> None:\n    dsn = os.environ[\"API__DATABASE__URL\"]\n    last: Exception | None = None\n    for _ in range(60):\n        try:\n            conn = await asyncpg.connect(dsn)\n            try:\n                await conn.fetchval(\"select 1\")\n                return\n            finally:\n                await conn.close()\n        except Exception as exc:\n            last = exc\n            await asyncio.sleep(1)\n    raise RuntimeError(f\"PostgreSQL не готов: {last}\")\n\n\nasyncio.run(main())'
	API__DATABASE__URL=postgresql://sync_user:sync_admin@localhost:55432/sync_test_db \
	API__DATABASE__REDIS_URL=redis://localhost:56379/0 \
	AUTH__JWT_SECRET=test-jwt-secret \
	UV_HTTP_TIMEOUT=120 \
	UV_HTTP_RETRIES=10 \
	bash -lc '\
	if [ -x .venv/bin/alembic ]; then \
		.venv/bin/alembic -c apps/api/alembic.ini upgrade head; \
	else \
		$(UV) run alembic -c apps/api/alembic.ini upgrade head; \
	fi'
	API__DATABASE__URL=postgresql://sync_user:sync_admin@localhost:55432/sync_test_db \
	API__DATABASE__REDIS_URL=redis://localhost:56379/0 \
	AUTH__JWT_SECRET=test-jwt-secret \
	UV_HTTP_TIMEOUT=120 \
	UV_HTTP_RETRIES=10 \
	bash -lc '\
	if [ -x .venv/bin/pytest ]; then \
		.venv/bin/pytest; \
	else \
		$(UV) run pytest; \
	fi'

.PHONY: api
api:
	API__DATABASE__URL=$$(jq -r '.api.database.url' conf.local.json) $(UV) run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: chat
chat:
	$(UV) run taskiq worker apps.api.src.realtime.broker:broker apps.api.src.realtime.tasks --workers 1 --log-level INFO

.PHONY: ui-install
ui-install:
	npm --prefix apps/api/static install

.PHONY: ui-build
ui-build: ui-install
	npm --prefix apps/api/static run build

.PHONY: ui-dev
ui-dev: ui-install
	npm --prefix apps/api/static run dev

.PHONY: ui
ui: ui-dev

.PHONY: api-ui
api-ui: ui-build
	API__DATABASE__URL=$$(jq -r '.api.database.url' conf.local.json) $(UV) run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: api-migrate
api-migrate:
	API__DATABASE__URL=$$(jq -r '.api.database.url' conf.local.json) $(UV) run alembic -c apps/api/alembic.ini upgrade head

