#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

echo "[install] AI SEO Manager dependencies..."

pip3 install --user -q -r "$ROOT/backend/requirements.txt"

cd "$ROOT/frontend"
npm install --silent

# Initialize SQLite DB schema on first install
cd "$ROOT/backend"
python3 -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
print('[install] database ready')
"

echo "[install] done"
