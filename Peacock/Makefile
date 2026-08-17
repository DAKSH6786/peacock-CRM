.PHONY: up down api web test migrate seed install

install:
	pip install -e ".[dev]"
	cd apps/web && npm install

up:
	docker compose up --build

down:
	docker compose down

migrate:
	alembic -c infra/migrations/alembic.ini upgrade head

seed:
	python3 infra/scripts/seed_dev.py

api:
	PYTHONPATH=.:apps/api:services:packages uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

test:
	JOB_BACKEND=memory pytest tests/ -q
	cd apps/web && npm test
