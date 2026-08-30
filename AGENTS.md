# AI SEO Manager Bot — Saba Tours & Travels

Based on SRS: *AI SEO Manager Bot — Saba Tours (Aug 2026)*.

## Quick start (automatic)

Services auto-start via `.cursor/environment.json` terminals:

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000/dashboard |
| **Websites** | http://localhost:3000/dashboard/websites |
| **Rankings** | http://localhost:3000/dashboard/rankings |
| **Reports** | http://localhost:3000/dashboard/reports |
| **Link Outreach** | http://localhost:3000/dashboard/link-outreach |
| **AI Chat** | http://localhost:3000/dashboard/chat |
| **API docs** | http://localhost:8000/docs |

**Demo login:** `demo@example.com` / `demo1234`  
**Portfolio:** onewaydrop.cab · sabacabs.com · punetomumbaicabservice.com

First login: click **Setup all 3 websites** on the dashboard onboarding card.

## Manual restart (if ports are down)

```bash
bash scripts/start-services.sh
```

## Testing

```bash
bash scripts/e2e-api.sh
bash scripts/start-services.sh
```

## Integrations (env vars)

- `SEMRUSH_API_KEY` — ranking sync via official API
- `OPENAI_API_KEY` — GPT chat
- `OPENPAGERANK_API_KEY` — link prospect scores

## Important notes

- `localhost:3000` on Windows only works if the app runs locally (`scripts/start-local-windows.bat`).
- Crawling may hit HTTP 429 — wait and retry.
- Human approval required before production SEO changes (SRS §24).

## Branch

Active development: `cursor/ai-seo-manager-mvp-4db6`
