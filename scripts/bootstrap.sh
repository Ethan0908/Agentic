#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in API keys before using discovery/drafts/deployments."
fi

docker compose up --build -d postgres backend frontend

echo "Waiting a few seconds for services..."
sleep 8

docker compose exec backend alembic upgrade head

echo "Ready. Dashboard: http://localhost:3000"
echo "API docs:  http://localhost:8000/docs"
