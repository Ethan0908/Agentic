#!/usr/bin/env bash
set -u

echo "whoami: $(whoami)"
echo "shell: ${SHELL:-unknown}"
echo "pwd: $(pwd)"
echo "PATH: $PATH"
echo

echo "command -v codex:"
command -v codex || true
echo

echo "type -a codex:"
type -a codex 2>/dev/null || true
echo

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
  "/opt/homebrew/bin/codex"; do
  [ -e "$p" ] && ls -la "$p"
done

echo
find "$HOME" -maxdepth 5 \( -name codex -o -name 'codex*' \) 2>/dev/null | head -50
