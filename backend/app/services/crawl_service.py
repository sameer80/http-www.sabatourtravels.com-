from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CrawlIssue,
    CrawlRun,
    CrawlStatus,
    InternalLink,
    Page,
    SeoOpportunity,
    Website,
)
from app.services.audit import analyze_technical_seo, detect_orphan_pages
from app.services.crawler import WebsiteCrawler
from app.services.opportunity import build_opportunities


async def run_website_crawl(db: AsyncSession, website_id: int) -> CrawlRun:
    result = await db.execute(select(Website).where(Website.id == website_id))
    website = result.scalar_one()

    crawl_run = CrawlRun(
        website_id=website.id,
        status=CrawlStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    db.add(crawl_run)
    await db.commit()
    await db.refresh(crawl_run)

    try:
        crawler = WebsiteCrawler(website.base_url)
        crawled_pages = await crawler.crawl()

        await db.execute(delete(InternalLink).where(InternalLink.website_id == website.id))
        await db.execute(delete(CrawlIssue).where(CrawlIssue.crawl_run_id == crawl_run.id))

        existing_pages_result = await db.execute(select(Page).where(Page.website_id == website.id))
        existing_pages = {p.url: p for p in existing_pages_result.scalars().all()}
        page_models: dict[str, Page] = {}

        for crawled in crawled_pages:
            page = existing_pages.get(crawled.url)
            if not page:
                page = Page(website_id=website.id, url=crawled.url, path=crawled.path)
                db.add(page)
                await db.flush()
            page.title = crawled.title
            page.meta_description = crawled.meta_description
            page.h1 = crawled.h1
            page.headings = crawled.headings
            page.word_count = crawled.word_count
            page.status_code = crawled.status_code
            page.canonical = crawled.canonical
            page.robots = crawled.robots
            page.has_schema = crawled.has_schema
            page.images_missing_alt = crawled.images_missing_alt
            page.internal_links_out = len(crawled.internal_links)
            page.last_crawled_at = datetime.now(UTC)
            page_models[crawled.url] = page

        await db.flush()
        url_to_page = {p.url: p for p in page_models.values()}

        link_counts: dict[int, int] = {}
        for crawled in crawled_pages:
            source = url_to_page.get(crawled.url)
            if not source:
                continue
            for target_url, anchor in crawled.internal_links:
                target = url_to_page.get(target_url)
                if not target:
                    continue
                db.add(
                    InternalLink(
                        website_id=website.id,
                        source_page_id=source.id,
                        target_page_id=target.id,
                        anchor_text=anchor,
                    )
                )
                link_counts[target.id] = link_counts.get(target.id, 0) + 1

        for page in page_models.values():
            page.internal_links_in = link_counts.get(page.id, 0)

        all_pages_result = await db.execute(select(Page).where(Page.website_id == website.id))
        all_pages = all_pages_result.scalars().all()
        detect_orphan_pages(all_pages)

        issues = analyze_technical_seo(
            crawled_pages,
            crawl_run,
            page_models,
            crawler.robots_txt,
            crawler.sitemap_urls,
        )
        for issue in issues:
            db.add(issue)

        crawl_run.pages_crawled = len(crawled_pages)
        crawl_run.issues_found = len(issues)
        crawl_run.status = CrawlStatus.COMPLETED
        crawl_run.completed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(crawl_run)
        return crawl_run
    except Exception as exc:  # noqa: BLE001
        crawl_run.status = CrawlStatus.FAILED
        crawl_run.error_message = str(exc)
        crawl_run.completed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(crawl_run)
        raise


async def refresh_opportunities(db: AsyncSession, website_id: int) -> list[SeoOpportunity]:
    from app.models import GscMetric, Keyword, RankHistory

    await db.execute(delete(SeoOpportunity).where(SeoOpportunity.website_id == website_id))

    keywords = (await db.execute(select(Keyword).where(Keyword.website_id == website_id))).scalars().all()
    pages = (await db.execute(select(Page).where(Page.website_id == website_id))).scalars().all()
    issues = (
        await db.execute(
            select(CrawlIssue).join(Page, CrawlIssue.page_id == Page.id).where(Page.website_id == website_id)
        )
    ).scalars().all()

    rank_map: dict[int, float | None] = {}
    rank_meta: dict[int, dict] = {}
    for keyword in keywords:
        rh = (
            await db.execute(
                select(RankHistory)
                .where(RankHistory.keyword_id == keyword.id)
                .order_by(RankHistory.recorded_at.desc(), RankHistory.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        rank_map[keyword.id] = rh.position if rh else None
        if rh:
            rank_meta[keyword.id] = {
                "search_volume": rh.search_volume,
                "keyword_difficulty": rh.keyword_difficulty,
                "position_change": rh.position_change,
            }

    gsc_rows = (await db.execute(select(GscMetric).where(GscMetric.website_id == website_id))).scalars().all()
    gsc_map = {row.query.lower(): row for row in gsc_rows}
    issues_by_page: dict[int, list[CrawlIssue]] = {}
    for issue in issues:
        if issue.page_id:
            issues_by_page.setdefault(issue.page_id, []).append(issue)

    opportunities = build_opportunities(keywords, rank_map, rank_meta, gsc_map, pages, issues_by_page)
    for opp in opportunities:
        db.add(opp)
    await db.commit()
    return opportunities
