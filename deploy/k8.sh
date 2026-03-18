#!/usr/bin/env bash
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

run_remote_via_ssh() {
  require_cmd jq
  require_cmd ssh

  if [[ ! -f "${CONF_LOCAL_JSON}" ]]; then
    echo "Не найден файл конфигурации: ${CONF_LOCAL_JSON}" >&2
    exit 1
  fi

  local ip login ssh_port
  ip="$(jq -er '.selectel.ip' "${CONF_LOCAL_JSON}")"
  login="$(jq -er '.selectel.login' "${CONF_LOCAL_JSON}")"
  ssh_port="$(jq -r '.selectel.ssh_port // "22"' "${CONF_LOCAL_JSON}")"

  # Сбрасываем старый ключ хоста — актуально после переустановки сервера.
  ssh-keygen -R "${ip}" 2>/dev/null || true
  ssh-keygen -R "[${ip}]:${ssh_port}" 2>/dev/null || true

  log "Подключаюсь к серверу: ${login}@${ip}:${ssh_port}"

  # SSH-ключ уже добавлен на сервер через панель Selectel.
  # Подключаемся только по ключу, без пароля.
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

MICROK8S_CHANNEL="${MICROK8S_CHANNEL:-1.29/stable}"

log "Установка MicroK8s (channel: ${MICROK8S_CHANNEL})"
if ! command -v microk8s >/dev/null 2>&1; then
  ${SUDO} snap install microk8s --classic --channel="${MICROK8S_CHANNEL}"
else
  log "MicroK8s уже установлен, пропускаем"
fi

log "Ожидание готовности кластера"
${SUDO} microk8s status --wait-ready

# Включает addon только если он ещё не активен.
enable_addon() {
  local addon="$1"
  if ${SUDO} microk8s status --format short 2>/dev/null | grep -q "^enabled:.*\b${addon}\b"; then
    log "Addon '${addon}' уже включён, пропускаем"
  else
    log "Включаем addon '${addon}'"
    ${SUDO} microk8s enable "${addon}"
  fi
}

log "Включение community-репозитория addon-ов"
enable_addon community

log "Включение базовых addon-ов"
enable_addon dns
enable_addon hostpath-storage
enable_addon helm
enable_addon metrics-server
enable_addon dashboard
enable_addon portainer

log "Итоговая проверка состояния кластера"
${SUDO} microk8s status --wait-ready

NODE_IP="$(ip -4 addr show scope global 2>/dev/null \
  | awk '/inet / {print $2}' \
  | awk -F/ '{print $1}' \
  | head -n 1 || true)"

if [[ -z "${NODE_IP}" ]]; then
  NODE_IP="IP_СЕРВЕРА"
fi

echo
echo "======================================"
echo " Установка завершена"
echo "======================================"
echo
echo "Portainer (веб-панель управления):"
echo "  http://${NODE_IP}:30777"
echo "  https://${NODE_IP}:30779"
echo "  При первом заходе создайте пользователя и пароль."
echo
echo "Kubernetes Dashboard:"
echo "  Токен для входа:"
echo "    ${SUDO} microk8s kubectl create token default"
echo "  Port-forward (выполнить на сервере, держать открытым):"
echo "    ${SUDO} microk8s kubectl port-forward -n kube-system service/kubernetes-dashboard 10443:443"
echo "  Открыть в браузере: https://127.0.0.1:10443"
echo "======================================"

REMOTE_SCRIPT
}

run_remote_via_ssh
