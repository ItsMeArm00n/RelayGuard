#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
if [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python; fi
exec "$PYTHON" run.py
