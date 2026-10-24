#!/bin/bash
set -e
cd "$(dirname "$0")"
PYTHON="$(command -v python3 || true)"
if [ -z "$PYTHON" ]; then echo "Please install Python 3.11 or newer."; exit 1; fi
if [ ! -f .venv/bin/python ]; then "$PYTHON" -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
printf '\nOpen http://127.0.0.1:8087 in your browser\n'
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8087
