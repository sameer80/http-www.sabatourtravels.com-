#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Lightweight per-boot check — terminals start the servers
if curl -sf http://localhost:8000/api/health >/dev/null 2>&1 && \
   curl -sf -o /dev/null http://localhost:3000 2>/dev/null; then
  echo "[start] services already running"
  exit 0
fi

echo "[start] launching services..."
bash "$ROOT/scripts/start-services.sh"
