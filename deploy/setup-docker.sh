#!/usr/bin/env bash
# Устанавливает Docker Engine на сервер и создаёт рабочую директорию /opt/sync
# с шаблоном .env файла. Запускается локально, все команды — по SSH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONF_LOCAL_JSON="${CONF_LOCAL_JSON:-${PROJECT_ROOT}/conf.local.json}"

log() {
  printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Локально не найдена команда '$1'. Установите её и повторите." >&2
    exit 1
  fi
}

require_cmd jq
require_cmd ssh

if [[ ! -f "${CONF_LOCAL_JSON}" ]]; then
  echo "Не найден файл конфигурации: ${CONF_LOCAL_JSON}" >&2
  exit 1
fi

ip="$(jq -er '.selectel.ip' "${CONF_LOCAL_JSON}")"
login="$(jq -er '.selectel.login' "${CONF_LOCAL_JSON}")"
ssh_port="$(jq -r '.selectel.ssh_port // "22"' "${CONF_LOCAL_JSON}")"

log "Подключаюсь к серверу: ${login}@${ip}:${ssh_port}"

ssh \
  -o StrictHostKeyChecking=accept-new \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  -p "${ssh_port}" \
  "${login}@${ip}" \
  "bash -s" <<'REMOTE_SCRIPT'

set -euo pipefail

log() {
  printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  SUDO="sudo"
fi

# ────────────────────────────────────────
# Docker Engine
# ────────────────────────────────────────
if command -v docker >/dev/null 2>&1; then
  log "Docker уже установлен: $(docker --version)"
else
  log "Устанавливаем Docker Engine"
  ${SUDO} apt-get update -qq
  ${SUDO} apt-get install -y -qq ca-certificates curl gnupg
  ${SUDO} install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | ${SUDO} gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  ${SUDO} chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
     https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | ${SUDO} tee /etc/apt/sources.list.d/docker.list > /dev/null
  ${SUDO} apt-get update -qq
  ${SUDO} apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  log "Docker установлен: $(docker --version)"
fi

# Добавляем текущего пользователя в группу docker, чтобы не нужен был sudo
CURRENT_USER="$(id -un)"
if ! id -nG "${CURRENT_USER}" | grep -qw docker; then
  ${SUDO} usermod -aG docker "${CURRENT_USER}"
  log "Пользователь ${CURRENT_USER} добавлен в группу docker (нужно перелогиниться)"
fi

# ────────────────────────────────────────
# Рабочая директория проекта
# ────────────────────────────────────────
log "Создаём /opt/sync"
${SUDO} mkdir -p /opt/sync
${SUDO} chown "${CURRENT_USER}:${CURRENT_USER}" /opt/sync

# Создаём .env только если его ещё нет — не перезаписываем уже заполненный
if [[ ! -f /opt/sync/.env ]]; then
  log "Создаём шаблон /opt/sync/.env"
  cat > /opt/sync/.env <<'ENVFILE'
# Заполните все значения перед первым деплоем!
IMAGE=ghcr.io/<GITHUB_USERNAME>/sync:latest
POSTGRES_PASSWORD=<strong-random-password>
JWT_SECRET=<random-64-char-hex>
ENVFILE
  echo
  echo "⚠  Заполните /opt/sync/.env на сервере перед первым деплоем:"
  echo "   ssh ${USER}@$(hostname -f) 'nano /opt/sync/.env'"
else
  log "/opt/sync/.env уже существует, не перезаписываем"
fi

echo
echo "======================================"
echo " Docker и /opt/sync готовы"
echo "======================================"

REMOTE_SCRIPT

log "Готово. Следующий шаг — заполните /opt/sync/.env на сервере."
