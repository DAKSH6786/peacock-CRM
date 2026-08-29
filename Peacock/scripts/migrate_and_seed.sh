#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/backend:$ROOT/backend/packages:$ROOT/backend/services:$ROOT/engines/seo:$ROOT/engines/aeo:$ROOT/engines/geo:$ROOT/engines/crawler:$ROOT/engines/competitor-intelligence:$ROOT/engines/citation-intelligence:$ROOT/engines/content-intelligence:$ROOT/engines/opportunity-engine:$ROOT/engines/llm-intelligence:$ROOT/engines/ai-visibility:$ROOT/engines/measurement:$ROOT/engines/experiment-engine:$ROOT/engines/learning-engine:$ROOT/plugins:$ROOT/agents:$ROOT/experts:$ROOT/publishing${PYTHONPATH:+:$PYTHONPATH}"
alembic -c database/migrations/alembic.ini upgrade head
python scripts/seed_dev.py
