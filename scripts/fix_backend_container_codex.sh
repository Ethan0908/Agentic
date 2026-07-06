#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${1:-agentic-backend-1}"
HOST_CODEX_DIR="${HOME}/.codex"

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: Docker container not found: $CONTAINER"
  echo "Existing containers:"
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  exit 1
fi

if [ ! -d "$HOST_CODEX_DIR" ]; then
  echo "ERROR: Host Codex directory not found: $HOST_CODEX_DIR"
  echo "Run Codex on the Raspberry Pi host first, then rerun this script."
  exit 1
fi

echo "== Host Codex files =="
ls -la "$HOST_CODEX_DIR"
echo

echo "== Container identity =="
CONTAINER_USER="$(docker exec "$CONTAINER" sh -lc 'id -un')"
CONTAINER_HOME="$(docker exec "$CONTAINER" sh -lc 'printf "%s" "$HOME"')"
echo "container: $CONTAINER"
echo "user:      $CONTAINER_USER"
echo "home:      $CONTAINER_HOME"
echo

echo "== Installing Codex CLI inside backend container =="
docker exec -u root "$CONTAINER" sh -lc '
set -e
if command -v codex >/dev/null 2>&1; then
  echo "Codex already present at $(command -v codex)"
  codex --version || true
  exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm missing; installing Node/npm first"
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y --no-install-recommends nodejs npm ca-certificates curl
    rm -rf /var/lib/apt/lists/*
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache nodejs npm ca-certificates curl
  else
    echo "ERROR: Cannot install npm because neither apt-get nor apk is available."
    exit 1
  fi
fi

npm install -g @openai/codex
if command -v codex >/dev/null 2>&1; then
  echo "Installed Codex at $(command -v codex)"
  codex --version
else
  echo "ERROR: npm finished but codex is still not on PATH."
  exit 1
fi
'

echo
echo "== Copying host Codex auth/config into backend container =="
docker exec -u root "$CONTAINER" sh -lc "rm -rf '$CONTAINER_HOME/.codex' '$CONTAINER_HOME/.codex.bak'"
docker cp "$HOST_CODEX_DIR" "$CONTAINER:$CONTAINER_HOME/.codex"

docker exec -u root "$CONTAINER" sh -lc "
set -e
# docker cp can behave differently when the destination exists across Docker versions.
# Ensure the final layout is always HOME/.codex/<files>, not HOME/.codex/.codex/<files>.
if [ -d '$CONTAINER_HOME/.codex/.codex' ]; then
  mv '$CONTAINER_HOME/.codex' '$CONTAINER_HOME/.codex.bak'
  mv '$CONTAINER_HOME/.codex.bak/.codex' '$CONTAINER_HOME/.codex'
  rm -rf '$CONTAINER_HOME/.codex.bak'
fi
mkdir -p '$CONTAINER_HOME/.codex'
# Some Codex installs tolerate a missing config, but this app checks/runs more reliably with it present.
[ -f '$CONTAINER_HOME/.codex/config.toml' ] || touch '$CONTAINER_HOME/.codex/config.toml'
chown -R '$CONTAINER_USER:$CONTAINER_USER' '$CONTAINER_HOME/.codex' 2>/dev/null || chown -R '$CONTAINER_USER' '$CONTAINER_HOME/.codex'
chmod 700 '$CONTAINER_HOME/.codex'
chmod 600 '$CONTAINER_HOME/.codex/config.toml'
"

echo
echo "== Testing Codex inside backend container =="
docker exec "$CONTAINER" sh -lc '
set -e
command -v codex
codex --version
ls -ld "$HOME/.codex"
ls -la "$HOME/.codex" | sed -n "1,30p"
test -f "$HOME/.codex/config.toml"
'

echo
echo "== Restarting backend container =="
docker restart "$CONTAINER" >/dev/null

echo
echo "Done. Test the generator again from the frontend."
echo "If generation still fails, run: docker logs --tail=300 $CONTAINER"
