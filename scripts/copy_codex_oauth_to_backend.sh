#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="${1:-}"
CONTAINER="${2:-agentic-backend-1}"
CONTAINER_HOME="$(docker exec "$CONTAINER" sh -lc 'printf "%s" "$HOME"')"
CONTAINER_USER="$(docker exec "$CONTAINER" sh -lc 'id -un')"

if [ -z "$SOURCE_PATH" ]; then
  echo "Usage: bash scripts/copy_codex_oauth_to_backend.sh <host-auth-file-or-folder> [container-name]"
  echo
  echo "Run this first to find the correct source path:"
  echo "  bash scripts/diagnose_codex_oauth.sh"
  exit 1
fi

if [ ! -e "$SOURCE_PATH" ]; then
  echo "ERROR: Source path does not exist: $SOURCE_PATH"
  exit 1
fi

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: Docker container not found: $CONTAINER"
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  exit 1
fi

echo "container: $CONTAINER"
echo "container home: $CONTAINER_HOME"
echo "container user: $CONTAINER_USER"
echo "source: $SOURCE_PATH"
echo

docker exec -u root "$CONTAINER" sh -lc "mkdir -p '$CONTAINER_HOME/.codex'"

if [ -d "$SOURCE_PATH" ]; then
  echo "Copying OAuth/config directory contents into $CONTAINER_HOME/.codex"
  docker cp "$SOURCE_PATH/." "$CONTAINER:$CONTAINER_HOME/.codex/"
else
  base="$(basename "$SOURCE_PATH")"
  echo "Copying OAuth/config file into $CONTAINER_HOME/.codex/$base"
  docker cp "$SOURCE_PATH" "$CONTAINER:$CONTAINER_HOME/.codex/$base"
fi

docker exec -u root "$CONTAINER" sh -lc "
set -e
chown -R '$CONTAINER_USER:$CONTAINER_USER' '$CONTAINER_HOME/.codex' 2>/dev/null || chown -R '$CONTAINER_USER' '$CONTAINER_HOME/.codex'
chmod 700 '$CONTAINER_HOME/.codex' || true
find '$CONTAINER_HOME/.codex' -type f -exec chmod 600 {} \; 2>/dev/null || true
"

echo
echo "Container Codex OAuth/config files now present:"
docker exec "$CONTAINER" sh -lc 'find "$HOME/.codex" -maxdepth 3 -type f -printf "%M %u:%g %p\n" 2>/dev/null | sed -n "1,80p"'

echo
echo "Testing Codex OAuth inside backend container:"
docker exec "$CONTAINER" sh -lc 'codex exec --skip-git-repo-check "Reply with OK only."'

echo
echo "Restarting backend container."
docker restart "$CONTAINER" >/dev/null

echo "Done. Try the frontend generator again."
