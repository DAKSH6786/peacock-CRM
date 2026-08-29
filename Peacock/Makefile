.PHONY: up down api web test migrate seed install

# Peacock One — single project root (Peacock/). Run these targets from
# inside this folder (or from the repo root via the top-level Makefile).
PYTHONPATH_DIRS := .:backend:backend/packages:backend/services:engines/seo:engines/aeo:engines/geo:engines/crawler:engines/competitor-intelligence:engines/citation-intelligence:engines/content-intelligence:engines/opportunity-engine:engines/llm-intelligence:engines/ai-visibility:engines/measurement:engines/experiment-engine:engines/learning-engine:plugins:agents:experts:publishing

install:
	pip install -e ".[dev]"
	cd frontend && npm install

up:
	docker compose up --build

down:
	docker compose down

migrate:
	alembic -c database/migrations/alembic.ini upgrade head

seed:
	python3 scripts/seed_dev.py

api:
	PYTHONPATH=$(PYTHONPATH_DIRS) uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

test:
	JOB_BACKEND=memory PYTHONPATH=$(PYTHONPATH_DIRS) pytest tests/ -q
	cd frontend && npm test
