from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.auth import log_action
from app.database import AsyncSessionLocal, get_db
from app.models import (
    Alert,
    CrawlIssue,
    CrawlRun,
    CrawlStatus,
    GscMetric,
    Keyword,
    Page,
    RankHistory,
    SeoOpportunity,
    SeoTask,
    TaskStatus,
    User,
    Website,
)
from app.schemas import (
    AiRecommendationOut,
    ApiSyncLogOut,
    ChatMessageCreate,
    ChatResponse,
    ChatMessageOut,
    CompetitorCreate,
    CompetitorOut,
    CrawlIssueOut,
    CrawlRunOut,
    DailyReportOut,
    DashboardOverview,
    GscMetricCreate,
    InternalLinkRecommendation,
    KeywordCreate,
    KeywordOut,
    OpportunityOut,
    PageOut,
    SerpAnalysisOut,
    SerpAnalysisRequest,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    LinkProspectSearchRequest,
    LinkProspectSearchOut,
    LinkProspectOut,
    LinkProspectPostRequest,
    WebsiteCreate,
    WebsiteOut,
)
from app.services.ai_agent import AiSeoAgent
from app.services.audit import recommend_internal_links
from app.services.crawl_service import refresh_opportunities, run_website_crawl
from app.services.opportunity import position_priority_zone, rank_change_label, zone_label
from app.services.reports import generate_daily_report
from app.services.semrush import sync_website_rankings
from app.services.serp import compare_page_with_serp, fetch_serp_competitors
from app.services.link_outreach import build_submission_plan, search_google_prospects
from app.models import Competitor, Backlink, LinkProspect, OutreachStatus

router = APIRouter(prefix="/websites", tags=["websites"])


async def _get_owned_website(db: AsyncSession, website_id: int, user: User) -> Website:
    result = await db.execute(select(Website).where(Website.id == website_id, Website.owner_id == user.id))
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website


async def _background_crawl(website_id: int) -> None:
    async with AsyncSessionLocal() as db:
        await run_website_crawl(db, website_id)
        await refresh_opportunities(db, website_id)


@router.post("", response_model=WebsiteOut)
async def create_website(
    payload: WebsiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = Website(owner_id=current_user.id, **payload.model_dump())
    db.add(website)
    await db.commit()
    await db.refresh(website)
    await log_action(db, "website_created", website_id=website.id, user_id=current_user.id)
    return website


@router.get("", response_model=list[WebsiteOut])
async def list_websites(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Website).where(Website.owner_id == current_user.id))
    return result.scalars().all()


@router.get("/{website_id}", response_model=WebsiteOut)
async def get_website(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await _get_owned_website(db, website_id, current_user)


@router.post("/{website_id}/crawl", response_model=CrawlRunOut)
async def start_crawl(
    website_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = await _get_owned_website(db, website_id, current_user)
    background_tasks.add_task(_background_crawl, website.id)
    await log_action(db, "crawl_started", website_id=website.id, user_id=current_user.id)
    return CrawlRunOut(
        id=0,
        status=CrawlStatus.PENDING,
        pages_crawled=0,
        issues_found=0,
        started_at=None,
        completed_at=None,
        error_message=None,
    )


@router.get("/{website_id}/crawl-runs", response_model=list[CrawlRunOut])
async def list_crawl_runs(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(
        select(CrawlRun).where(CrawlRun.website_id == website_id).order_by(CrawlRun.id.desc())
    )
    return result.scalars().all()


@router.get("/{website_id}/issues", response_model=list[CrawlIssueOut])
async def list_issues(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(
        select(CrawlIssue, Page.url)
        .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
        .join(Page, CrawlIssue.page_id == Page.id, isouter=True)
        .where(CrawlRun.website_id == website_id)
        .order_by(CrawlIssue.id.desc())
    )
    issues = []
    for issue, page_url in result.all():
        item = CrawlIssueOut.model_validate(issue)
        item.page_url = page_url
        issues.append(item)
    return issues


@router.get("/{website_id}/pages", response_model=list[PageOut])
async def list_pages(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(select(Page).where(Page.website_id == website_id).order_by(Page.path))
    return result.scalars().all()


@router.post("/{website_id}/keywords", response_model=KeywordOut)
async def add_keyword(
    website_id: int,
    payload: KeywordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    keyword = Keyword(website_id=website_id, **payload.model_dump(exclude={"position"}))
    db.add(keyword)
    await db.flush()
    if payload.position is not None:
        db.add(RankHistory(keyword_id=keyword.id, page_id=payload.target_page_id, position=payload.position))
    await db.commit()
    await db.refresh(keyword)
    await refresh_opportunities(db, website_id)
    out = KeywordOut.model_validate(keyword)
    out.latest_position = payload.position
    return out


@router.get("/{website_id}/keywords", response_model=list[KeywordOut])
async def list_keywords(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    keywords = (await db.execute(select(Keyword).where(Keyword.website_id == website_id))).scalars().all()
    output: list[KeywordOut] = []
    for keyword in keywords:
        history = (
            await db.execute(
                select(RankHistory)
                .where(RankHistory.keyword_id == keyword.id)
                .order_by(RankHistory.recorded_at.desc(), RankHistory.id.desc())
                .limit(5)
            )
        ).scalars().all()
        latest = history[0] if history else None
        item = KeywordOut.model_validate(keyword)
        item.latest_position = latest.position if latest else None
        item.previous_position = latest.previous_position if latest else None
        item.position_change = latest.position_change if latest else None
        item.position_trend = rank_change_label(history)
        item.priority_zone = zone_label(item.latest_position)
        item.search_volume = latest.search_volume if latest else None
        item.keyword_difficulty = latest.keyword_difficulty if latest else None
        output.append(item)
    return output


@router.get("/{website_id}/keywords/{keyword_id}/history", response_model=list[dict])
async def keyword_history(
    website_id: int,
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    rows = (
        await db.execute(
            select(RankHistory).where(RankHistory.keyword_id == keyword_id).order_by(RankHistory.recorded_at.asc())
        )
    ).scalars().all()
    return [{"position": r.position, "recorded_at": r.recorded_at.isoformat()} for r in rows]


@router.post("/{website_id}/gsc-metrics")
async def add_gsc_metric(
    website_id: int,
    payload: GscMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    metric = GscMetric(website_id=website_id, **payload.model_dump())
    db.add(metric)
    await db.commit()
    await refresh_opportunities(db, website_id)
    return {"status": "ok"}


@router.get("/{website_id}/opportunities", response_model=list[OpportunityOut])
async def list_opportunities(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(
        select(SeoOpportunity)
        .where(SeoOpportunity.website_id == website_id)
        .order_by(SeoOpportunity.score.desc())
    )
    return result.scalars().all()


@router.post("/{website_id}/opportunities/refresh", response_model=list[OpportunityOut])
async def recompute_opportunities(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    return await refresh_opportunities(db, website_id)


@router.get("/{website_id}/tasks", response_model=list[TaskOut])
async def list_tasks(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(select(SeoTask).where(SeoTask.website_id == website_id).order_by(SeoTask.id.desc()))
    return result.scalars().all()


@router.post("/{website_id}/tasks", response_model=TaskOut)
async def create_task(
    website_id: int,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    task = SeoTask(website_id=website_id, **payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{website_id}/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    website_id: int,
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(select(SeoTask).where(SeoTask.id == task_id, SeoTask.website_id == website_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{website_id}/chat", response_model=ChatResponse)
async def chat(
    website_id: int,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = await _get_owned_website(db, website_id, current_user)
    agent = AiSeoAgent(db, website)
    reply, evidence, tasks = await agent.respond(payload.message)
    conversation = await agent.save_conversation(
        current_user.id, payload.message, reply, evidence, payload.conversation_id
    )
    return ChatResponse(
        conversation_id=conversation.id,
        reply=ChatMessageOut(role="assistant", content=reply, evidence=evidence),
        tasks_created=[TaskOut.model_validate(t) for t in tasks],
    )


@router.get("/{website_id}/dashboard", response_model=DashboardOverview)
async def dashboard(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    website = await _get_owned_website(db, website_id, current_user)
    pages_count = await db.scalar(select(func.count()).select_from(Page).where(Page.website_id == website_id))
    issues_count = await db.scalar(
        select(func.count())
        .select_from(CrawlIssue)
        .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
        .where(CrawlRun.website_id == website_id)
    )
    severity_rows = await db.execute(
        select(CrawlIssue.severity, func.count())
        .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
        .where(CrawlRun.website_id == website_id)
        .group_by(CrawlIssue.severity)
    )
    issues_by_severity = {row[0].value: row[1] for row in severity_rows.all()}
    keywords = (await db.execute(select(Keyword).where(Keyword.website_id == website_id))).scalars().all()
    top_3 = top_10 = top_20 = high_opportunity = opportunity_zone = 0
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
            top_3 += 1
        if latest <= 10:
            top_10 += 1
        if latest <= 20:
            top_20 += 1
        zone = position_priority_zone(latest)
        if zone == "high":
            high_opportunity += 1
        if 11 <= latest <= 20:
            opportunity_zone += 1

    seo_score = 0.0
    if keywords:
        ranking_score = min(50, (top_10 / len(keywords)) * 50)
        technical_score = max(0, 30 - min(30, issues_count or 0))
        coverage_score = min(20, pages_count or 0)
        seo_score = round(ranking_score + technical_score + coverage_score, 1)
    pending_tasks = await db.scalar(
        select(func.count()).select_from(SeoTask).where(
            SeoTask.website_id == website_id, SeoTask.status != TaskStatus.COMPLETED
        )
    )
    opportunities = (
        await db.execute(
            select(SeoOpportunity)
            .where(SeoOpportunity.website_id == website_id)
            .order_by(SeoOpportunity.score.desc())
            .limit(5)
        )
    ).scalars().all()
    alerts = (
        await db.execute(
            select(Alert).where(Alert.website_id == website_id).order_by(Alert.created_at.desc()).limit(5)
        )
    ).scalars().all()
    return DashboardOverview(
        website=WebsiteOut.model_validate(website),
        seo_score=seo_score,
        total_pages=pages_count or 0,
        total_issues=issues_count or 0,
        issues_by_severity=issues_by_severity,
        total_keywords=len(keywords),
        keywords_top_3=top_3,
        keywords_top_10=top_10,
        keywords_top_20=top_20,
        keywords_high_opportunity=high_opportunity,
        keywords_top_10_legacy=top_10,
        keywords_opportunity_zone=opportunity_zone,
        pending_tasks=pending_tasks or 0,
        top_opportunities=[OpportunityOut.model_validate(o) for o in opportunities],
        recent_alerts=[
            {"title": a.title, "severity": a.severity.value, "message": a.message} for a in alerts
        ],
    )


@router.post("/{website_id}/serp-analysis", response_model=SerpAnalysisOut)
async def serp_analysis(
    website_id: int,
    payload: SerpAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    competitors = await fetch_serp_competitors(payload.keyword)
    user_page_data = None
    if payload.page_id:
        page = (
            await db.execute(select(Page).where(Page.id == payload.page_id, Page.website_id == website_id))
        ).scalar_one_or_none()
        if page:
            user_page_data = {
                "path": page.path,
                "title": page.title,
                "h1": page.h1,
                "word_count": page.word_count,
                "meta_description": page.meta_description,
                "internal_links_in": page.internal_links_in,
                "has_schema": page.has_schema,
            }
    comparison = compare_page_with_serp(user_page_data, competitors)
    return SerpAnalysisOut(
        keyword=payload.keyword,
        user_page=user_page_data,
        competitors=competitors,
        content_gaps=comparison["content_gaps"],
        recommendations=comparison["recommendations"],
    )


@router.get("/{website_id}/internal-links", response_model=list[InternalLinkRecommendation])
async def internal_links(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    pages = (await db.execute(select(Page).where(Page.website_id == website_id))).scalars().all()
    return recommend_internal_links(pages)


@router.post("/{website_id}/competitors", response_model=CompetitorOut)
async def add_competitor(
    website_id: int,
    payload: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    competitor = Competitor(website_id=website_id, **payload.model_dump())
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.get("/{website_id}/competitors", response_model=list[CompetitorOut])
async def list_competitors(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    return (await db.execute(select(Competitor).where(Competitor.website_id == website_id))).scalars().all()


@router.get("/{website_id}/backlinks/gap")
async def backlink_gap(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    competitor_links = (
        await db.execute(select(Backlink).where(Backlink.competitor_id.is_not(None)).limit(100))
    ).scalars().all()
    site_links = (
        await db.execute(select(Backlink).where(Backlink.website_id == website_id))
    ).scalars().all()
    site_domains = {b.source_domain for b in site_links}
    gaps = [
        {
            "source_domain": link.source_domain,
            "source_url": link.source_url,
            "anchor_text": link.anchor_text,
            "competitor_target": link.target_url,
        }
        for link in competitor_links
        if link.source_domain not in site_domains
    ]
    return {
        "gap_count": len(gaps),
        "gaps": gaps[:50],
        "note": "Connect a backlink data provider to populate live gap analysis.",
    }


@router.post("/{website_id}/link-prospects/search", response_model=LinkProspectSearchOut)
async def search_link_prospects(
    website_id: int,
    payload: LinkProspectSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = await _get_owned_website(db, website_id, current_user)
    raw = await search_google_prospects(payload.keyword)
    filtered = [
        item
        for item in raw
        if item["domain_authority"] >= payload.min_da and item["page_authority"] >= payload.min_pa
    ]

    saved: list[LinkProspect] = []
    for item in filtered:
        existing = (
            await db.execute(
                select(LinkProspect).where(
                    LinkProspect.website_id == website_id,
                    LinkProspect.prospect_url == item["prospect_url"],
                    LinkProspect.keyword == payload.keyword,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.domain_authority = item["domain_authority"]
            existing.page_authority = item["page_authority"]
            existing.page_rank = item["page_rank"]
            saved.append(existing)
            continue
        prospect = LinkProspect(
            website_id=website_id,
            keyword=payload.keyword,
            target_url=payload.target_url,
            prospect_url=item["prospect_url"],
            prospect_domain=item["prospect_domain"],
            prospect_title=item.get("prospect_title"),
            prospect_type=item["prospect_type"],
            domain_authority=item["domain_authority"],
            page_authority=item["page_authority"],
            page_rank=item["page_rank"],
            suggested_anchor=payload.anchor_text or payload.keyword,
            google_query=item.get("google_query"),
            outreach_status=OutreachStatus.READY,
        )
        db.add(prospect)
        saved.append(prospect)

    await db.commit()
    for p in saved:
        await db.refresh(p)

    plan = build_submission_plan(payload.target_url, payload.keyword, payload.anchor_text)
    await log_action(
        db,
        "link_prospects_searched",
        website_id=website.id,
        user_id=current_user.id,
        details={"keyword": payload.keyword, "found": len(saved)},
    )
    return LinkProspectSearchOut(
        keyword=payload.keyword,
        target_url=payload.target_url,
        found=len(saved),
        prospects=[LinkProspectOut.model_validate(p) for p in saved],
        submission_plan=plan,
    )


@router.get("/{website_id}/link-prospects", response_model=list[LinkProspectOut])
async def list_link_prospects(
    website_id: int,
    min_da: float = 0,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    query = select(LinkProspect).where(LinkProspect.website_id == website_id, LinkProspect.domain_authority >= min_da)
    if status:
        query = query.where(LinkProspect.outreach_status == OutreachStatus(status))
    result = await db.execute(query.order_by(LinkProspect.domain_authority.desc()))
    return result.scalars().all()


@router.patch("/{website_id}/link-prospects/{prospect_id}", response_model=LinkProspectOut)
async def update_link_prospect(
    website_id: int,
    prospect_id: int,
    payload: LinkProspectPostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_website(db, website_id, current_user)
    result = await db.execute(
        select(LinkProspect).where(LinkProspect.id == prospect_id, LinkProspect.website_id == website_id)
    )
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    prospect.outreach_status = OutreachStatus(payload.outreach_status)
    if payload.posted_url:
        prospect.posted_url = payload.posted_url
    if payload.notes:
        prospect.notes = payload.notes
    if payload.outreach_status in ("posted", "live"):
        from datetime import UTC, datetime

        prospect.posted_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(prospect)
    await log_action(
        db,
        "link_prospect_updated",
        website_id=website_id,
        user_id=current_user.id,
        details={"prospect_id": prospect_id, "status": payload.outreach_status},
    )
    return prospect


@router.get("/{website_id}/reports/daily", response_model=DailyReportOut)
async def daily_report(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    website = await _get_owned_website(db, website_id, current_user)
    report = await generate_daily_report(db, website)
    return DailyReportOut(**report)


@router.get("/{website_id}/recommendations", response_model=list[AiRecommendationOut])
async def ai_recommendations(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await _get_owned_website(db, website_id, current_user)
    opportunities = (
        await db.execute(
            select(SeoOpportunity)
            .where(SeoOpportunity.website_id == website_id)
            .order_by(SeoOpportunity.score.desc())
            .limit(25)
        )
    ).scalars().all()
    output: list[AiRecommendationOut] = []
    for opp in opportunities:
        zone = (opp.signals or {}).get("priority_zone", "MEDIUM")
        priority = "High" if opp.score >= 70 else "Medium" if opp.score >= 45 else "Low"
        if "CRITICAL" in opp.title.upper() or opp.opportunity_type == "technical_seo":
            priority = "Critical" if opp.score >= 60 else priority
        owner = "Developer" if opp.opportunity_type == "technical_seo" else "SEO + Content"
        output.append(
            AiRecommendationOut(
                id=opp.id,
                title=opp.title,
                opportunity_type=opp.opportunity_type,
                score=opp.score,
                evidence=opp.evidence,
                signals=opp.signals,
                priority=priority,
                suggested_owner=owner,
                validation_method="Re-crawl affected URLs and monitor ranking movement next cycle.",
                status="open",
            )
        )
    return output


@router.post("/{website_id}/sync/semrush", response_model=ApiSyncLogOut)
async def sync_semrush_rankings(
    website_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    website = await _get_owned_website(db, website_id, current_user)
    log = await sync_website_rankings(db, website)
    if log.status == "completed":
        await refresh_opportunities(db, website_id)
    await log_action(
        db,
        "semrush_sync",
        website_id=website.id,
        user_id=current_user.id,
        details={"status": log.status, "records": log.records_synced},
    )
    return log
