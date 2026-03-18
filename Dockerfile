# Этап 1: сборка SolidJS-фронтенда
FROM node:22-alpine AS frontend

WORKDIR /frontend
COPY apps/api/static/package*.json ./
RUN npm ci
COPY apps/api/static/ ./
RUN npm run build


# Этап 2: Python-образ приложения
FROM python:3.14-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Зависимости устанавливаем отдельным слоем — кешируются пока pyproject.toml не меняется
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Исходники
COPY core/ core/
COPY apps/ apps/
COPY conf.json ./

# Собранный фронтенд кладём туда, откуда main.py его раздаёт
COPY --from=frontend /frontend/dist/ apps/api/static/dist/

EXPOSE 8000
