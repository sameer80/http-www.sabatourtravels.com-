#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

start_tmux() {
  local name="$1"
  local dir="$2"
  local cmd="$3"
  tmux -f /exec-daemon/tmux.portal.conf has-session -t "=$name" 2>/dev/null || \
    tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$name" -c "$dir" -- "${SHELL:-bash}" -l
  tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$name:0.0" C-c 2>/dev/null || true
  sleep 0.5
  tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$name:0.0" "$cmd" C-m
}

echo "Installing dependencies..."
pip3 install -q -r "$ROOT/backend/requirements.txt"
(cd "$ROOT/frontend" && npm install --silent)

echo "Starting backend on :8000..."
start_tmux "backend-api" "$ROOT/backend" \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd $ROOT/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo "Starting frontend on :3000..."
start_tmux "frontend-dev" "$ROOT/frontend" \
  "cd $ROOT/frontend && npm run dev"

echo "Waiting for services..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1 && \
     curl -sf -o /dev/null http://localhost:3000 2>/dev/null; then
    echo "OK  Frontend: http://localhost:3000"
    echo "OK  Backend:  http://localhost:8000"
    echo "OK  Login:    demo@example.com / demo1234"
    exit 0
  fi
  sleep 1
done

echo "Services did not become ready in 30s. Check tmux sessions: backend-api, frontend-dev"
exit 1
