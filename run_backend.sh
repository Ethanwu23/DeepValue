#!/bin/bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR/backend"
exec .venv/bin/langgraph dev --host 127.0.0.1 --port 2024 --no-browser --no-reload --allow-blocking
