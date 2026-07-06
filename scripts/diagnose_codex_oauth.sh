#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${1:-agentic-backend-1}"

echo "== Host Codex executable =="
command -v codex || true
codex --version || true
echo

echo "== Host Codex OAuth/config candidates =="
for dir in \
  "$HOME/.codex" \
  "$HOME/.config/codex" \
  "$HOME/.config/openai-codex" \
  "$HOME/.config/openai/codex" \
  "$HOME/.local/share/codex"; do
  if [ -d "$dir" ]; then
    echo "-- $dir"
    find "$dir" -maxdepth 3 -type f \( \
      -name 'auth.json' -o \
      -name 'config.toml' -o \
      -name '*token*' -o \
      -name '*credential*' -o \
      -name '*session*' \
    \) -printf '%M %u:%g %p\n' 2>/dev/null || true
  fi
done

echo
 echo "== Broader host search for likely Codex auth files =="
find "$HOME" -maxdepth 6 -type f \( \
  -path '*/.codex/*' -o \
  -path '*/codex/*' -o \
  -path '*/openai-codex/*' \
\) \( \
  -name 'auth.json' -o \
  -name 'config.toml' -o \
  -name '*token*' -o \
  -name '*credential*' -o \
  -name '*session*' \
\) -printf '%M %u:%g %p\n' 2>/dev/null | head -100 || true

echo
if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "== Container Codex executable =="
  docker exec "$CONTAINER" sh -lc 'command -v codex || true; codex --version || true'
  echo
  echo "== Container Codex home =="
  docker exec "$CONTAINER" sh -lc 'echo HOME=$HOME; find "$HOME/.codex" -maxdepth 3 -type f -printf "%M %u:%g %p\n" 2>/dev/null || true'
fi

echo
cat <<'EOF'
Next step:
- If you see a host auth.json or token/session file, copy it into the backend with:
  bash scripts/copy_codex_oauth_to_backend.sh <path-to-auth-folder-or-file>
- If you do not see any auth file, run Codex OAuth login on the host first:
  codex
  # choose Sign in with ChatGPT
EOF
