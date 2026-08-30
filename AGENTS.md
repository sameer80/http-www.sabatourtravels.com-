# AI SEO Manager — Cloud Agent Guide

## Quick start (automatic)

Services auto-start via `.cursor/environment.json` terminals:

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000/dashboard |
| **Link Outreach** | http://localhost:3000/dashboard/link-outreach |
| **AI Chat** | http://localhost:3000/dashboard/chat |
| **API docs** | http://localhost:8000/docs |

**Demo login:** `demo@example.com` / `demo1234`  
**Website:** sabacabs.com (Saba Cabs)

## Manual restart (if ports are down)

```bash
bash scripts/start-services.sh
```

## Project structure

- `backend/` — FastAPI + SQLite (local) / PostgreSQL (Docker)
- `frontend/` — Next.js 14 dashboard
- `scripts/` — start, test, and Windows helper scripts

## Testing

```bash
bash scripts/e2e-api.sh          # API smoke tests
bash scripts/start-services.sh   # start backend :8000 + frontend :3000
```

## Important notes

- `localhost:3000` in **your Windows browser** only works if the app runs **on your PC**.
  Run `scripts/start-local-windows.bat` on Windows, OR use Cursor's **Ports** panel for cloud agents.
- Crawling sabacabs.com may hit HTTP 429 rate limits — wait and retry.
- Optional secrets: `OPENAI_API_KEY`, `OPENPAGERANK_API_KEY` in environment secrets.

## Branch

Active development: `cursor/ai-seo-manager-mvp-4db6`
