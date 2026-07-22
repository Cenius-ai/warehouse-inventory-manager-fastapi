#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Installing dependencies ==="
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements.txt

echo "=== Verifying import ==="
python3 -c 'import main; print("OK: main.py imports cleanly")'

echo "=== Seeding database ==="
python3 -m seed

echo ""
echo "=== Setup complete ==="
echo "Start the server:  uvicorn main:app --host 0.0.0.0 --port 8000"
echo "Demo login:        cenius@cenius.ai / cenius"
