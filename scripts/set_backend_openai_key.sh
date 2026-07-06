#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${1:-agentic-backend-1}"
HOST_ENV_FILE="${PWD}/.env.local"
CONTAINER_ENV_FILE="/app/.env.local"

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
  tmp="$(mktemp)"
  grep -v '^OPENAI_API_KEY=' "$HOST_ENV_FILE" > "$tmp"
  cat "$tmp" > "$HOST_ENV_FILE"
  rm -f "$tmp"
fi
printf 'OPENAI_API_KEY=%s\n' "$OPENAI_API_KEY" >> "$HOST_ENV_FILE"

echo "Wrote host env file: $HOST_ENV_FILE"

docker exec -u root "$CONTAINER" sh -lc "touch '$CONTAINER_ENV_FILE' && chmod 600 '$CONTAINER_ENV_FILE'"
docker exec -i -u root "$CONTAINER" sh -lc "
set -e
TMP=\$(mktemp)
if [ -f '$CONTAINER_ENV_FILE' ]; then
  grep -v '^OPENAI_API_KEY=' '$CONTAINER_ENV_FILE' > \$TMP || true
fi
cat > '$CONTAINER_ENV_FILE' <<'EOF'
$(grep -v '^OPENAI_API_KEY=' "$HOST_ENV_FILE" || true)
OPENAI_API_KEY=$OPENAI_API_KEY
EOF
chmod 600 '$CONTAINER_ENV_FILE'
rm -f \$TMP
"

echo "Wrote container env file: $CONTAINER:$CONTAINER_ENV_FILE"

echo "Testing env visibility inside backend container:"
docker exec "$CONTAINER" sh -lc 'python - <<"PY"
from backend.app.services.env_loader import load_local_env
env = load_local_env()
print("OPENAI_API_KEY loaded:", "yes" if env.get("OPENAI_API_KEY") else "no")
print("CODEX_COMMAND:", env.get("CODEX_COMMAND", "codex"))
PY'

echo "Testing Codex authentication inside backend container:"
docker exec "$CONTAINER" sh -lc 'OPENAI_API_KEY=$(grep -m1 "^OPENAI_API_KEY=" /app/.env.local | cut -d= -f2-) codex exec --skip-git-repo-check "Reply with OK only."'

echo "Restarting backend container."
docker restart "$CONTAINER" >/dev/null

echo "Done. Try the frontend generator again."
