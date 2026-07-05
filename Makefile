.PHONY: up down logs migrate shell-backend lint

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

shell-backend:
	docker compose exec backend bash

lint:
	docker compose exec backend python -m compileall app
