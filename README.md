# AI SEO Manager Bot — Saba Tours & Travels

AI-powered SEO intelligence platform for **onewaydrop.cab**, **sabacabs.com**, and **punetomumbaicabservice.com**.

Based on the SRS: *AI SEO Manager Bot — Saba Tours & Travels (Aug 2026)*.

## Stack

- **Frontend:** Next.js 14 + Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL + pgvector (SQLite for local dev)
- **Queue:** Redis + Celery
- **Integrations:** SEMrush API, Google Search Console (planned), PageSpeed Insights (planned)

## Quick start

### Cloud Agent (automatic)
Services start via `.cursor/environment.json`. Open **Ports → 3000** in Cursor, or:

- Dashboard: http://localhost:3000/dashboard
- Login: `demo@example.com` / `demo1234`
- Click **Setup all 3 websites** on first login

Manual restart: `bash scripts/start-services.sh`

### Windows PC (local)
Double-click: `scripts\start-local-windows.bat`

### Docker
```bash
docker compose up --build
```

## SRS websites

| Domain | Positioning |
|--------|-------------|
| onewaydrop.cab | One-way cab specialist |
| sabacabs.com | Cab + airport + outstation |
| punetomumbaicabservice.com | Pune–Mumbai specialist |

## MVP features

- Three-website portfolio bootstrap with priority keywords
- SRS keyword opportunity zones (Protect / Top 10 / High / Medium / Low)
- Website crawler and technical SEO audit
- Rank tracking with historical snapshots
- AI recommendations with evidence, priority and owner
- Daily SEO reports (SRS §27 workflow)
- SEMrush API sync (when `SEMRUSH_API_KEY` is set)
- SERP competitor analysis, internal links, backlink gap, link outreach
- SEO task board and AI chat

## Environment variables

| Variable | Description |
|----------|-------------|
| `SEMRUSH_API_KEY` | SEMrush API for ranking/backlink sync |
| `OPENAI_API_KEY` | Optional — GPT-powered chat |
| `OPENPAGERANK_API_KEY` | Link prospect authority scores |
| `SECRET_KEY` | JWT signing key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis for Celery |

## API highlights

- `POST /api/auth/register` — create account
- `POST /api/auth/login` — get JWT token
- `POST /api/websites` — add website
- `POST /api/websites/{id}/crawl` — start crawl
- `POST /api/websites/{id}/keywords` — track keyword
- `GET /api/websites/{id}/dashboard` — overview metrics
- `POST /api/websites/{id}/chat` — AI SEO manager

## Phases

1. **Phase 1:** Crawler, technical audit, keywords, rank tracking, dashboard
2. **Phase 2:** AI analysis, opportunity score, SERP/content gap, chatbot, tasks
3. **Phase 3:** Automation, alerts, reports, CMS actions, learning loop
