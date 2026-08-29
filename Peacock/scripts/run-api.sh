#!/usr/bin/env bash
# Start the FastAPI backend used by the Peacock One dashboard.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  bash "$ROOT/scripts/ensure-python.sh"
fi

# shellcheck source=pythonpath.sh
source "$ROOT/scripts/pythonpath.sh"
export PYTHONPATH="$ROOT:${PYTHONPATH}"

exec .venv/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
