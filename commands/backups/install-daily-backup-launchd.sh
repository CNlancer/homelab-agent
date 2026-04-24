#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
AGENT_LABEL="com.homelab-agent.daily-backup"
PLIST_PATH="$HOME/Library/LaunchAgents/${AGENT_LABEL}.plist"
RUNNER_PATH="${ROOT_DIR}/commands/backups/run-unraid-backup.sh"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "${ROOT_DIR}/var/log"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${AGENT_LABEL}</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>${RUNNER_PATH}</string>
  </array>

  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>3</integer>
    <key>Minute</key>
    <integer>20</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>${ROOT_DIR}/var/log/launchd-unraid-backup.out.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT_DIR}/var/log/launchd-unraid-backup.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "Installed: $PLIST_PATH"
echo "Schedule: daily at 03:20"
echo "Manual run: ${RUNNER_PATH}"
