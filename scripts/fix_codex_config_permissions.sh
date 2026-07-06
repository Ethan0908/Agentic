#!/usr/bin/env bash
set -euo pipefail

CODEX_DIR="$HOME/.codex"
CONFIG_FILE="$CODEX_DIR/config.toml"

if [ ! -d "$CODEX_DIR" ]; then
  echo "No Codex directory found at $CODEX_DIR"
  echo "Run /usr/bin/codex first to create/login, then rerun this script if permissions fail."
  exit 1
fi

echo "Current Codex permissions:"
ls -ld "$CODEX_DIR" || true
[ -e "$CONFIG_FILE" ] && ls -l "$CONFIG_FILE" || echo "No config.toml yet"
echo

echo "Path ownership chain:"
namei -l "$CONFIG_FILE" 2>/dev/null || true
echo

echo "Repairing ownership and permissions for user: $USER"
sudo chown -R "$USER:$USER" "$CODEX_DIR"
chmod 700 "$CODEX_DIR"
if [ -e "$CONFIG_FILE" ]; then
  chmod 600 "$CONFIG_FILE"
fi

echo
echo "After repair:"
ls -ld "$CODEX_DIR"
[ -e "$CONFIG_FILE" ] && ls -l "$CONFIG_FILE" || true
echo

echo "Testing /usr/bin/codex --version:"
/usr/bin/codex --version

echo
echo "If this works, run:"
echo "python3 -m backend.app.services.codex_scratch_generator leads/example-plumber.json --preview --codex-command /usr/bin/codex"
