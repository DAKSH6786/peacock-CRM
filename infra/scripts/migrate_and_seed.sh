#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/apps/api:$ROOT/services:$ROOT/packages${PYTHONPATH:+:$PYTHONPATH}"
alembic -c infra/migrations/alembic.ini upgrade head
python infra/scripts/seed_dev.py
