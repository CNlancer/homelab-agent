#!/bin/zsh
set -euo pipefail

AGENT_LABEL="com.homelab-agent.daily-backup"
PLIST_PATH="$HOME/Library/LaunchAgents/${AGENT_LABEL}.plist"

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

echo "Removed: $PLIST_PATH"
