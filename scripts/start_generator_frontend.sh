#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x "/usr/bin/codex" ]; then
  echo "ERROR: /usr/bin/codex is not executable."
  echo "Run: /usr/bin/codex --version"
  exit 1
fi

python3 -m backend.app.services.generator_frontend_server
