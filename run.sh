#!/bin/bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p .run
if lsof -nP -iTCP:2024 -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "2024 或 5173 端口已被占用，请先停止已有服务。"
  exit 1
fi
echo $$ > .run/app.pid
BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  trap - EXIT INT TERM
  if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
  rm -f .run/app.pid
}
trap cleanup EXIT
trap 'exit 0' INT TERM
bash "$PROJECT_DIR/run_backend.sh" > .run/backend.log 2>&1 &
BACKEND_PID=$!
bash "$PROJECT_DIR/run_fontend.sh" > .run/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "页面：http://127.0.0.1:5173/app/"
echo "后端：http://127.0.0.1:2024"
echo "日志：$PROJECT_DIR/.run/"
echo "按 Ctrl+C 停止；后台启动时向 .run/app.pid 中的进程发送 TERM。"
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done
echo "服务已退出，请检查 .run/backend.log 和 .run/frontend.log。"
exit 1
