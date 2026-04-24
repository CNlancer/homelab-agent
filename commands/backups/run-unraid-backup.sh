#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

export PATH="/opt/homebrew/bin:/usr/local/bin:/Users/lancer/Library/Python/3.9/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "[homelab-agent] uv not found in PATH=$PATH" >&2
  exit 127
fi

mkdir -p var/log
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_PATH="var/log/unraid-backup-${TIMESTAMP}.log"

{
  echo "[homelab-agent] backup start ${TIMESTAMP}"
  uv run homelab-agent \
    --target-type unraid \
    --target-name unraid \
    --action backup_boot_config_to_local \
    --arguments '{"local_backup_root":"var/backups/unraid"}' \
    --risk-level safe_read
  echo "[homelab-agent] backup done ${TIMESTAMP}"
  echo "[homelab-agent] next: append router backup command here when mikrotik export action is ready"
} | tee "$LOG_PATH"
