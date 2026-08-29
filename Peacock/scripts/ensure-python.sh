#!/usr/bin/env bash
# Create / refresh the Python virtualenv used by `npm run dev` and `npm test`.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run Peacock One's API." >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e ".[dev]"
echo "Python environment ready: $ROOT/.venv"
