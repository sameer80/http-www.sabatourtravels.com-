# AI SEO Manager

AI-powered SEO intelligence, ranking, competitor, backlink and action-management platform.

## Stack

- **Frontend:** Next.js 14 + Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL + pgvector
- **Queue:** Redis + Celery
- **Crawler:** httpx + BeautifulSoup

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## MVP features

- Website onboarding and crawling
- Technical SEO audit with severity levels
- Keyword tracking and rank history
- SEO opportunity scoring (0-100)
- SERP competitor analysis
- Internal link recommendations
- Backlink gap framework
- AI SEO chatbot with evidence-based responses
- SEO task board
- Scheduled crawl/opportunity refresh via Celery

## Product rules

- Never guarantees #1 Google ranking
- Recommendations include evidence/signals
- Automated changes require explicit approval
- Historical data retained for learning loop

## Environment variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Optional — enables GPT-powered chat responses |
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
