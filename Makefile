SHELL := /bin/bash

PROJECT_NAME := sync
UV := uv
DOCKER_COMPOSE := docker-compose -f docker-compose.dev.yml

.PHONY: dev
dev:
	$(DOCKER_COMPOSE) up -d

.PHONY: test
test:
	$(UV) run pytest

.PHONY: api
api:
	API__DATABASE__URL=$$(jq -r '.api.database.url' conf.local.json) $(UV) run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: api-migrate
api-migrate:
	API__DATABASE__URL=$$(jq -r '.api.database.url' conf.local.json) $(UV) run alembic -c apps/api/alembic.ini upgrade head

