.PHONY: up down api web test migrate seed install

# Convenience wrappers — project root is Peacock/
PEACOCK := Peacock

install:
	cd $(PEACOCK) && pip install -e ".[dev]"
	cd $(PEACOCK)/apps/web && npm install

up:
	cd $(PEACOCK) && docker compose up --build

down:
	cd $(PEACOCK) && docker compose down

migrate:
	cd $(PEACOCK) && alembic -c infra/migrations/alembic.ini upgrade head

seed:
	cd $(PEACOCK) && python3 infra/scripts/seed_dev.py

api:
	cd $(PEACOCK) && PYTHONPATH=.:apps/api:services:packages uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd $(PEACOCK)/apps/web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

test:
	cd $(PEACOCK) && JOB_BACKEND=memory PYTHONPATH=.:apps/api:services:packages pytest tests/ -q
	cd $(PEACOCK)/apps/web && npm test
