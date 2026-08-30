from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.auth import log_action
from app.database import get_db
from app.models import CrawlIssue, CrawlRun, Keyword, Page, RankHistory, SeoTask, TaskStatus, User, Website
from app.schemas import PortfolioOverview, WebsiteOut, CrossLinkPlanResponse, CrossLinkPlanItem
from app.services.opportunity import position_priority_zone
from app.services.portfolio import bootstrap_saba_tours_portfolio
from app.services.crawl_service import refresh_opportunities
from app.services.cross_links import build_cross_link_plan

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


async def _keyword_counts(db: AsyncSession, website_id: int) -> dict[str, int]:
    keywords = (await db.execute(select(Keyword).where(Keyword.website_id == website_id))).scalars().all()
    counts = {"top_3": 0, "top_10": 0, "top_20": 0, "high_opportunity": 0, "total": len(keywords)}
    for keyword in keywords:
        latest = (
            await db.execute(
                select(RankHistory.position)
                .where(RankHistory.keyword_id == keyword.id)
                .order_by(RankHistory.recorded_at.desc(), RankHistory.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest is None:
            continue
        if latest <= 3:
            counts["top_3"] += 1
        if latest <= 10:
            counts["top_10"] += 1
        if latest <= 20:
            counts["top_20"] += 1
        zone = position_priority_zone(latest)
        if zone == "high":
            counts["high_opportunity"] += 1
    return counts


def _seo_score(*, pages: int, issues: int, top_10: int, total_keywords: int) -> float:
    if total_keywords == 0:
        return 0.0
    ranking_score = min(50, (top_10 / total_keywords) * 50)
    technical_score = max(0, 30 - min(30, issues))
    coverage_score = min(20, pages)
    return round(ranking_score + technical_score + coverage_score, 1)


@router.post("/bootstrap/saba-tours", response_model=list[WebsiteOut])
async def bootstrap_saba_tours(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    websites = await bootstrap_saba_tours_portfolio(db, current_user.id)
    for website in websites:
        await refresh_opportunities(db, website.id)
    await log_action(
        db,
        "portfolio_bootstrapped",
        user_id=current_user.id,
        details={"domains": [w.domain for w in websites]},
    )
    return websites


@router.get("/overview", response_model=PortfolioOverview)
async def portfolio_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    websites = (
        await db.execute(select(Website).where(Website.owner_id == current_user.id).order_by(Website.id))
    ).scalars().all()
    site_summaries = []
    totals = {
        "websites": len(websites),
        "keywords": 0,
        "top_3": 0,
        "top_10": 0,
        "top_20": 0,
        "high_opportunity": 0,
        "issues": 0,
        "open_tasks": 0,
    }

    for website in websites:
        counts = await _keyword_counts(db, website.id)
        pages_count = await db.scalar(select(func.count()).select_from(Page).where(Page.website_id == website.id))
        issues_count = await db.scalar(
            select(func.count())
            .select_from(CrawlIssue)
            .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
            .where(CrawlRun.website_id == website.id)
        )
        open_tasks = await db.scalar(
            select(func.count()).select_from(SeoTask).where(
                SeoTask.website_id == website.id, SeoTask.status != TaskStatus.COMPLETED
            )
        )
        totals["keywords"] += counts["total"]
        totals["top_3"] += counts["top_3"]
        totals["top_10"] += counts["top_10"]
        totals["top_20"] += counts["top_20"]
        totals["high_opportunity"] += counts["high_opportunity"]
        totals["issues"] += issues_count or 0
        totals["open_tasks"] += open_tasks or 0

        site_summaries.append(
            {
                "website_id": website.id,
                "name": website.name,
                "domain": website.domain,
                "positioning": website.positioning,
                "seo_focus": website.seo_focus,
                "seo_score": _seo_score(
                    pages=pages_count or 0,
                    issues=issues_count or 0,
                    top_10=counts["top_10"],
                    total_keywords=counts["total"],
                ),
                "keywords_top_3": counts["top_3"],
                "keywords_top_10": counts["top_10"],
                "keywords_top_20": counts["top_20"],
                "keywords_high_opportunity": counts["high_opportunity"],
                "technical_issues": issues_count or 0,
                "open_tasks": open_tasks or 0,
                "pages_crawled": pages_count or 0,
            }
        )

    return PortfolioOverview(
        organization="Saba Tours & Travels",
        websites=[WebsiteOut.model_validate(w) for w in websites],
        totals=totals,
        site_summaries=site_summaries,
    )


@router.get("/cross-links/plan", response_model=CrossLinkPlanResponse)
async def cross_links_plan(
    current_user: User = Depends(get_current_user),
):
    plan = build_cross_link_plan()
    return CrossLinkPlanResponse(
        organization="Saba Tours & Travels",
        total_links=len(plan),
        plan=[CrossLinkPlanItem.model_validate(item) for item in plan],
        selenium_script="scripts/post-portfolio-links-selenium.py",
        config_example="scripts/link-post-config.example.json",
    )
