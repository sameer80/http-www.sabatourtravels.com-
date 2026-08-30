from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlIssue, CrawlRun, Keyword, RankHistory, SeoOpportunity, SeoTask, TaskStatus, Website
from app.services.opportunity import position_priority_zone, zone_label


async def generate_daily_report(db: AsyncSession, website: Website) -> dict[str, Any]:
    """Generate SRS section 27 style daily AI SEO report."""
    keywords = (await db.execute(select(Keyword).where(Keyword.website_id == website.id))).scalars().all()
    keyword_reports: list[dict[str, Any]] = []

    for keyword in keywords[:10]:
        history = (
            await db.execute(
                select(RankHistory)
                .where(RankHistory.keyword_id == keyword.id)
                .order_by(RankHistory.recorded_at.desc(), RankHistory.id.desc())
                .limit(2)
            )
        ).scalars().all()
        if not history:
            continue
        current = history[0]
        previous = history[1] if len(history) > 1 else None
        prev_pos = previous.position if previous else current.previous_position
        curr_pos = current.position
        change = None
        if prev_pos is not None and curr_pos is not None:
            change = round(prev_pos - curr_pos, 0)
        status = "Stable"
        if change is not None:
            if change > 0:
                status = "Improving"
            elif change < 0:
                status = "Declining"

        zone = zone_label(curr_pos)
        priority_action = _priority_action(curr_pos, keyword.query)
        keyword_reports.append(
            {
                "keyword": keyword.query,
                "previous_position": prev_pos,
                "current_position": curr_pos,
                "change": change,
                "status": status,
                "priority_zone": zone,
                "priority_action": priority_action,
                "owner": "SEO + Developer",
                "validation": "Re-crawl page and monitor ranking trend after changes.",
            }
        )

    issues_count = await db.scalar(
        select(func.count())
        .select_from(CrawlIssue)
        .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
        .where(CrawlRun.website_id == website.id)
    )
    pending_tasks = await db.scalar(
        select(func.count()).select_from(SeoTask).where(
            SeoTask.website_id == website.id, SeoTask.status != TaskStatus.COMPLETED
        )
    )
    top_opps = (
        await db.execute(
            select(SeoOpportunity)
            .where(SeoOpportunity.website_id == website.id)
            .order_by(SeoOpportunity.score.desc())
            .limit(5)
        )
    ).scalars().all()

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "website": {
            "name": website.name,
            "domain": website.domain,
            "positioning": website.positioning,
        },
        "summary": {
            "keywords_tracked": len(keywords),
            "technical_issues": issues_count or 0,
            "open_tasks": pending_tasks or 0,
            "top_opportunities": len(top_opps),
        },
        "keyword_movements": keyword_reports,
        "top_recommendations": [
            {
                "title": o.title,
                "score": o.score,
                "evidence": o.evidence,
                "type": o.opportunity_type,
            }
            for o in top_opps
        ],
        "workflow_note": "Measure → Diagnose → Recommend → Assign → Implement → Re-crawl → Re-measure → Report",
    }


def _priority_action(position: float | None, keyword: str) -> str:
    zone = position_priority_zone(position)
    if zone == "protect":
        return f"Monitor volatility for '{keyword}' and protect Top 3 rankings against competitor movement."
    if zone == "top_10":
        return f"Optimize on-page content and internal links to push '{keyword}' from Top 10 into Top 3."
    if zone == "high":
        return (
            f"Strengthen internal links from relevant service pages and review content gaps against "
            f"SERP competitors for '{keyword}'."
        )
    if zone == "medium":
        return f"Build supporting topical content, internal links and authority signals for '{keyword}'."
    return f"Assess search intent and page relevance before investing in '{keyword}'."
