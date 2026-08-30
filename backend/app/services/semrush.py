"""SEMrush API integration — official API only, credentials via environment variables."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ApiSyncLog, Keyword, RankHistory, Website

logger = logging.getLogger(__name__)

SEMRUSH_BASE = "https://api.semrush.com/"


class SemrushClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.semrush_api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _request(self, params: dict[str, str]) -> str:
        if not self.api_key:
            raise RuntimeError("SEMRUSH_API_KEY is not configured")
        query = {**params, "key": self.api_key}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(SEMRUSH_BASE, params=query)
            response.raise_for_status()
            return response.text

    async def fetch_domain_organic_positions(
        self, domain: str, database: str = "in", limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fetch organic keyword positions for a domain (SEMrush domain_organic report)."""
        raw = await self._request(
            {
                "type": "domain_organic",
                "domain": domain,
                "database": database,
                "display_limit": str(limit),
                "export_columns": "Ph,Po,Nq,Kd,Ur",
            }
        )
        rows: list[dict[str, Any]] = []
        lines = [line for line in raw.strip().splitlines() if line and not line.startswith("Keyword")]
        for line in lines:
            parts = line.split(";")
            if len(parts) < 5:
                continue
            keyword, position, volume, difficulty, url = parts[:5]
            try:
                pos = float(position.replace(",", "."))
            except ValueError:
                pos = None
            rows.append(
                {
                    "keyword": keyword.strip(),
                    "position": pos,
                    "search_volume": int(float(volume or 0)),
                    "keyword_difficulty": float(difficulty or 0),
                    "ranking_url": url.strip(),
                }
            )
        return rows


async def sync_website_rankings(
    db: AsyncSession,
    website: Website,
    *,
    client: SemrushClient | None = None,
) -> ApiSyncLog:
    """Sync ranking snapshots from SEMrush when API key is available."""
    semrush = client or SemrushClient()
    log = ApiSyncLog(
        website_id=website.id,
        provider="semrush",
        sync_type="rankings",
        status="running",
    )
    db.add(log)
    await db.flush()

    if not semrush.configured:
        log.status = "skipped"
        log.message = "SEMRUSH_API_KEY not set — configure in environment variables"
        log.completed_at = datetime.now(UTC)
        await db.commit()
        return log

    try:
        rows = await semrush.fetch_domain_organic_positions(website.domain)
        keywords = (
            await db.execute(
                __import__("sqlalchemy").select(Keyword).where(Keyword.website_id == website.id)
            )
        ).scalars().all()
        keyword_lookup = {k.query.lower(): k for k in keywords}

        synced = 0
        for row in rows:
            keyword = keyword_lookup.get(row["keyword"].lower())
            if not keyword:
                keyword = Keyword(
                    website_id=website.id,
                    query=row["keyword"],
                    country=website.country,
                    city=website.city,
                    language=website.language,
                )
                db.add(keyword)
                await db.flush()
                keyword_lookup[row["keyword"].lower()] = keyword

            previous = (
                await db.execute(
                    __import__("sqlalchemy")
                    .select(RankHistory)
                    .where(RankHistory.keyword_id == keyword.id)
                    .order_by(RankHistory.recorded_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

            prev_pos = previous.position if previous else None
            curr_pos = row["position"]
            position_change = None
            if prev_pos is not None and curr_pos is not None:
                position_change = round(prev_pos - curr_pos, 1)

            db.add(
                RankHistory(
                    keyword_id=keyword.id,
                    position=curr_pos,
                    previous_position=prev_pos,
                    position_change=position_change,
                    search_volume=row.get("search_volume", 0),
                    keyword_difficulty=row.get("keyword_difficulty", 0.0),
                    ranking_url=row.get("ranking_url"),
                    search_engine="google",
                )
            )
            synced += 1

        log.status = "completed"
        log.records_synced = synced
        log.message = f"Synced {synced} keyword ranking records from SEMrush"
    except Exception as exc:
        logger.exception("SEMrush sync failed for %s", website.domain)
        log.status = "failed"
        log.message = str(exc)[:500]

    log.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(log)
    return log
