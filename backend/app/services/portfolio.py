"""Bootstrap Saba Tours & Travels portfolio websites and seed keywords."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.saba_tours_portfolio import SABA_TOURS_PORTFOLIO, PortfolioWebsite
from app.models import Keyword, RankHistory, Website


async def bootstrap_saba_tours_portfolio(db: AsyncSession, owner_id: int) -> list[Website]:
    created: list[Website] = []
    existing = (
        await db.execute(select(Website).where(Website.owner_id == owner_id))
    ).scalars().all()
    existing_domains = {w.domain.lower() for w in existing}

    for spec in SABA_TOURS_PORTFOLIO:
        if spec.domain.lower() in existing_domains:
            site = next(w for w in existing if w.domain.lower() == spec.domain.lower())
            created.append(site)
            continue

        website = Website(
            owner_id=owner_id,
            name=spec.name,
            domain=spec.domain,
            base_url=spec.base_url,
            country="IN",
            city="Pune",
            language="en",
            positioning=spec.positioning,
            seo_focus=spec.seo_focus,
            seotooladda_report_url=(
                "https://smr.seotooladda.com/seo/31026440" if spec.domain == "sabacabs.com" else None
            ),
        )
        db.add(website)
        await db.flush()
        await _seed_keywords(db, website, spec)
        created.append(website)

    await db.commit()
    for site in created:
        await db.refresh(site)
    return created


async def _seed_keywords(db: AsyncSession, website: Website, spec: PortfolioWebsite) -> None:
    """Seed demo ranking positions until SEMrush/GSC sync is connected."""
    demo_positions = [18, 27, 8, 14, 31, 5, 22, 11, 35, 3]
    for idx, query in enumerate(spec.default_keywords):
        position = demo_positions[idx % len(demo_positions)]
        keyword = Keyword(
            website_id=website.id,
            query=query,
            country=website.country,
            city=website.city,
            language=website.language,
            device="desktop",
            is_primary=True,
        )
        db.add(keyword)
        await db.flush()
        prev = position + random.randint(1, 6)
        now = datetime.now(UTC)
        db.add(
            RankHistory(
                keyword_id=keyword.id,
                position=float(prev),
                search_engine="google",
                search_volume=800 + idx * 120,
                keyword_difficulty=35 + idx * 4,
                intent="transactional",
                priority=zone_priority(position),
                recorded_at=now,
            )
        )
        db.add(
            RankHistory(
                keyword_id=keyword.id,
                position=float(position),
                previous_position=float(prev),
                position_change=round(prev - position, 1),
                search_engine="google",
                search_volume=800 + idx * 120,
                keyword_difficulty=35 + idx * 4,
                intent="transactional",
                priority=zone_priority(position),
                recorded_at=now + timedelta(seconds=1),
            )
        )


def zone_priority(position: float) -> str:
    if position <= 3:
        return "protect"
    if position <= 10:
        return "top_10"
    if position <= 30:
        return "high"
    if position <= 50:
        return "medium"
    return "low"
