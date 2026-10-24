#!/bin/bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR/frontend"
exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
