# Деплой Sync

## Принцип

GitHub Actions собирает Docker-образ и пушит его в `ghcr.io`.  
Потом по SSH заходит на сервер и перезапускает `api` и `chat_worker` с новым образом.

```
git push → GitHub Actions → ghcr.io → SSH → docker compose up -d
```

---

## Структура файлов

| Файл | Назначение |
|------|-----------|
| `Dockerfile` | Мульти-стейдж: Node (фронт) → Python (API + worker) |
| `docker-compose.prod.yml` | Все сервисы: postgres, redis, api, chat_worker, migrate |
| `.github/workflows/deploy.yml` | CI/CD пайплайн |
| `deploy/setup-docker.sh` | Одноразовая подготовка сервера (Docker Engine + /opt/sync) |
| `deploy/k8.sh` | Установка MicroK8s + Portainer (веб-панель K8s) |

---

## Первоначальная настройка (один раз)

### 1. Подготовить сервер

```bash
bash deploy/setup-docker.sh
```

Устанавливает Docker Engine на сервер и создаёт `/opt/sync/.env`.

### 2. Добавить секреты в GitHub

Идёте в GitHub → репозиторий → Settings → Secrets and variables → Actions.  
`.env` на сервере **не нужно создавать вручную** — GitHub Actions запишет его автоматически при каждом деплое.

Сгенерировать значения для секретов:
```bash
openssl rand -hex 32   # POSTGRES_PASSWORD
openssl rand -hex 32   # JWT_SECRET
```

### 3. Первый запуск (postgres + redis)

На сервере:
```bash
cd /opt/sync
docker compose -f docker-compose.prod.yml up -d postgres redis
# Подождать ~5 секунд, потом миграции:
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml up -d
```

### 4. Добавить SSH-ключ для GitHub Actions

Сгенерировать выделенную пару ключей (локально):
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/sync_deploy
```

Добавить публичный ключ на сервер:
```bash
ssh-copy-id -i ~/.ssh/sync_deploy.pub root@84.38.184.105
```

### 5. Добавить секреты в GitHub

Идёте в GitHub → репозиторий → Settings → Secrets and variables → Actions:

| Секрет | Значение |
|--------|---------|
| `SERVER_HOST` | `84.38.184.105` |
| `SERVER_USER` | `root` |
| `SERVER_SSH_KEY` | содержимое `~/.ssh/sync_deploy` (приватный ключ) |
| `GHCR_TOKEN` | Personal Access Token с правом `read:packages` |
| `POSTGRES_PASSWORD` | вывод `openssl rand -hex 32` |
| `JWT_SECRET` | вывод `openssl rand -hex 32` |

---

## Как работает деплой

При каждом `git push` в `main`:

1. GitHub Actions собирает Docker-образ с тегом `sha-<commit>` и `latest`
2. Пушит в `ghcr.io/<username>/sync`
3. Копирует `docker-compose.prod.yml` на сервер в `/opt/sync/`
4. По SSH: обновляет `IMAGE=` в `.env`, делает `docker compose pull`, прогоняет миграции, рестартует `api` и `chat_worker`

Postgres и Redis при этом **не перезапускаются**.

---

## Ручной деплой (без GitHub Actions)

```bash
# Собрать и запушить образ
docker build -t ghcr.io/<username>/sync:latest .
docker push ghcr.io/<username>/sync:latest

# На сервере
ssh root@84.38.184.105
cd /opt/sync
docker compose -f docker-compose.prod.yml pull api chat_worker
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml up -d --no-deps api chat_worker
```
