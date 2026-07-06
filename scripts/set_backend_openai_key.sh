#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${1:-agentic-backend-1}"
HOST_ENV_FILE="${PWD}/.env.local"
CONTAINER_ENV_FILE="/app/.env.local"
TMP_ENV_FILE="$(mktemp)"
trap 'rm -f "$TMP_ENV_FILE"' EXIT

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: Docker container not found: $CONTAINER"
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
  printf "Paste OPENAI_API_KEY or Codex access token for backend container: " >&2
  stty -echo
  read -r OPENAI_API_KEY
  stty echo
  printf "\n" >&2
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "ERROR: OPENAI_API_KEY was empty."
  exit 1
fi

mkdir -p "$(dirname "$HOST_ENV_FILE")"
touch "$HOST_ENV_FILE"
chmod 600 "$HOST_ENV_FILE"
if grep -q '^OPENAI_API_KEY=' "$HOST_ENV_FILE"; then
  grep -v '^OPENAI_API_KEY=' "$HOST_ENV_FILE" > "$TMP_ENV_FILE"
  cat "$TMP_ENV_FILE" > "$HOST_ENV_FILE"
fi
printf 'OPENAI_API_KEY=%s\n' "$OPENAI_API_KEY" >> "$HOST_ENV_FILE"
chmod 600 "$HOST_ENV_FILE"

echo "Wrote host env file: $HOST_ENV_FILE"

# Build a sanitized temp env file and copy it into the container. This avoids putting the key in docker exec args.
grep -v '^OPENAI_API_KEY=' "$HOST_ENV_FILE" > "$TMP_ENV_FILE" || true
printf 'OPENAI_API_KEY=%s\n' "$OPENAI_API_KEY" >> "$TMP_ENV_FILE"
chmod 600 "$TMP_ENV_FILE"

docker cp "$TMP_ENV_FILE" "$CONTAINER:/tmp/agentic-env.local"
docker exec -u root "$CONTAINER" sh -lc "mv /tmp/agentic-env.local '$CONTAINER_ENV_FILE' && chmod 600 '$CONTAINER_ENV_FILE'"

echo "Wrote container env file: $CONTAINER:$CONTAINER_ENV_FILE"

echo "Testing env visibility inside backend container:"
docker exec "$CONTAINER" sh -lc 'python - <<"PY"
from backend.app.services.env_loader import load_local_env
env = load_local_env()
print("OPENAI_API_KEY loaded:", "yes" if env.get("OPENAI_API_KEY") else "no")
print("CODEX_COMMAND:", env.get("CODEX_COMMAND", "codex"))
PY'

echo "Testing Codex authentication inside backend container:"
docker exec "$CONTAINER" sh -lc 'set -a; . /app/.env.local; set +a; codex exec --skip-git-repo-check "Reply with OK only."'

echo "Restarting backend container."
docker restart "$CONTAINER" >/dev/null

echo "Done. Try the frontend generator again."
