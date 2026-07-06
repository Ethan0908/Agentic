#!/usr/bin/env bash
set -u

echo "whoami: $(whoami)"
echo "shell: ${SHELL:-unknown}"
echo "pwd: $(pwd)"
echo "PATH: $PATH"
echo

echo "command -v codex:"
CODEX_PATH="$(command -v codex || true)"
echo "${CODEX_PATH:-not found}"
echo

echo "type -a codex:"
type -a codex 2>/dev/null || true
echo

if [ -n "${CODEX_PATH:-}" ]; then
  echo "selected codex path:"
  ls -la "$CODEX_PATH" || true
  echo

  echo "selected codex symlink target:"
  readlink -f "$CODEX_PATH" || true
  echo

  REAL_CODEX="$(readlink -f "$CODEX_PATH" || true)"
  if [ -n "${REAL_CODEX:-}" ]; then
    echo "real codex target details:"
    ls -la "$REAL_CODEX" || true
    file "$REAL_CODEX" 2>/dev/null || true
    namei -l "$REAL_CODEX" 2>/dev/null || true
    echo
  fi

  echo "codex --version direct test:"
  "$CODEX_PATH" --version || true
  echo
fi

echo "npm global bin/root:"
npm bin -g 2>/dev/null || true
npm root -g 2>/dev/null || true
echo

echo "possible codex files:"
for p in \
  "$HOME/.local/bin/codex" \
  "$HOME/.npm-global/bin/codex" \
  "$HOME/.nvm/versions/node"/*/bin/codex \
  "/usr/local/bin/codex" \
  "/usr/bin/codex" \
  "/bin/codex"; do
  [ -e "$p" ] && ls -la "$p"
done

echo
find "$HOME" -maxdepth 5 \( -name codex -o -name 'codex*' \) 2>/dev/null | head -50
