from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from app.models import CrawlIssue, CrawlRun, Page, Severity
from app.services.crawler import CrawledPage


def analyze_technical_seo(
    pages: list[CrawledPage],
    crawl_run: CrawlRun,
    page_models: dict[str, Page],
    robots_txt: str | None,
    sitemap_urls: list[str],
) -> list[CrawlIssue]:
    issues: list[CrawlIssue] = []
    titles: Counter[str] = Counter()
    metas: Counter[str] = Counter()

    if not robots_txt:
        issues.append(
            CrawlIssue(
                crawl_run_id=crawl_run.id,
                issue_type="missing_robots_txt",
                severity=Severity.MEDIUM,
                message="robots.txt is missing or unreachable",
                evidence={"url": "/robots.txt"},
            )
        )

    if not sitemap_urls:
        issues.append(
            CrawlIssue(
                crawl_run_id=crawl_run.id,
                issue_type="missing_sitemap",
                severity=Severity.MEDIUM,
                message="No XML sitemap discovered",
                evidence={},
            )
        )

    for crawled in pages:
        page = page_models.get(crawled.url)
        page_id = page.id if page else None

        if crawled.status_code == 404:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="http_404",
                    severity=Severity.CRITICAL,
                    message=f"Page returns 404: {crawled.path}",
                    evidence={"url": crawled.url, "status_code": 404},
                )
            )
        elif crawled.status_code == 0:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="fetch_error",
                    severity=Severity.HIGH,
                    message=f"Could not fetch page: {crawled.path}",
                    evidence={"url": crawled.url},
                )
            )
        elif crawled.status_code >= 400:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="http_error",
                    severity=Severity.HIGH,
                    message=f"HTTP {crawled.status_code} on {crawled.path}",
                    evidence={"url": crawled.url, "status_code": crawled.status_code},
                )
            )

        if len(crawled.redirect_chain) > 2:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="redirect_chain",
                    severity=Severity.MEDIUM,
                    message=f"Redirect chain detected on {crawled.path}",
                    evidence={"chain": crawled.redirect_chain},
                )
            )

        if not crawled.title:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="missing_title",
                    severity=Severity.HIGH,
                    message=f"Missing title tag on {crawled.path}",
                    evidence={"url": crawled.url},
                )
            )
        elif crawled.title:
            titles[crawled.title.lower()] += 1

        if not crawled.meta_description:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="missing_meta_description",
                    severity=Severity.MEDIUM,
                    message=f"Missing meta description on {crawled.path}",
                    evidence={"url": crawled.url},
                )
            )
        elif crawled.meta_description:
            metas[crawled.meta_description.lower()] += 1

        if not crawled.h1:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="missing_h1",
                    severity=Severity.MEDIUM,
                    message=f"Missing H1 on {crawled.path}",
                    evidence={"url": crawled.url},
                )
            )
        elif len(crawled.headings.get("h1", [])) > 1:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="multiple_h1",
                    severity=Severity.LOW,
                    message=f"Multiple H1 tags on {crawled.path}",
                    evidence={"h1_count": len(crawled.headings.get("h1", []))},
                )
            )

        if crawled.word_count < 150:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="thin_content",
                    severity=Severity.MEDIUM,
                    message=f"Thin content detected on {crawled.path} ({crawled.word_count} words)",
                    evidence={"word_count": crawled.word_count},
                )
            )

        if crawled.images_missing_alt > 0:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="missing_image_alt",
                    severity=Severity.LOW,
                    message=f"{crawled.images_missing_alt} images missing alt text on {crawled.path}",
                    evidence={"count": crawled.images_missing_alt},
                )
            )

        if crawled.canonical:
            canonical_path = urlparse(crawled.canonical).path or "/"
            if canonical_path != crawled.path and crawled.canonical != crawled.url:
                issues.append(
                    CrawlIssue(
                        crawl_run_id=crawl_run.id,
                        page_id=page_id,
                        issue_type="canonical_mismatch",
                        severity=Severity.MEDIUM,
                        message=f"Canonical points elsewhere on {crawled.path}",
                        evidence={"canonical": crawled.canonical},
                    )
                )

        if crawled.robots and "noindex" in crawled.robots.lower():
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    page_id=page_id,
                    issue_type="noindex",
                    severity=Severity.HIGH,
                    message=f"Page marked noindex: {crawled.path}",
                    evidence={"robots": crawled.robots},
                )
            )

    for title, count in titles.items():
        if count > 1:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    issue_type="duplicate_title",
                    severity=Severity.HIGH,
                    message=f"Duplicate title used on {count} pages",
                    evidence={"title": title, "count": count},
                )
            )

    for meta, count in metas.items():
        if count > 1:
            issues.append(
                CrawlIssue(
                    crawl_run_id=crawl_run.id,
                    issue_type="duplicate_meta_description",
                    severity=Severity.MEDIUM,
                    message=f"Duplicate meta description used on {count} pages",
                    evidence={"meta_description": meta[:120], "count": count},
                )
            )

    return issues


def detect_orphan_pages(pages: list[Page]) -> list[Page]:
    orphans = []
    for page in pages:
        if page.internal_links_in == 0 and page.path not in ("/", ""):
            page.is_orphan = True
            orphans.append(page)
    return orphans


def recommend_internal_links(pages: list[Page], limit: int = 20) -> list[dict]:
    recommendations: list[dict] = []
    commercial_pages = sorted(
        [p for p in pages if any(k in p.path.lower() for k in ("cab", "booking", "service", "tour"))],
        key=lambda p: p.internal_links_in,
    )
    authority_pages = sorted(pages, key=lambda p: p.internal_links_in, reverse=True)

    for target in commercial_pages:
        if target.internal_links_in >= 3:
            continue
        for source in authority_pages:
            if source.id == target.id:
                continue
            if any(r["target_page"] == target.path for r in recommendations):
                continue
            anchor = (target.h1 or target.title or target.path.strip("/").replace("-", " "))[:80]
            recommendations.append(
                {
                    "source_page": source.path,
                    "target_page": target.path,
                    "anchor_text": anchor,
                    "reason": f"{target.path} has weak internal authority ({target.internal_links_in} incoming links)",
                }
            )
            if len(recommendations) >= limit:
                return recommendations
    return recommendations
