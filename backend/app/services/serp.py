from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import settings


async def fetch_serp_competitors(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    """Fetch simplified SERP competitor snapshots. Uses public search HTML when no API key is set."""
    competitors: list[dict[str, Any]] = []
    query = keyword.replace(" ", "+")

    try:
        async with httpx.AsyncClient(
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AI-SEO-Manager/1.0)"},
            follow_redirects=True,
        ) as client:
            response = await client.get(f"https://html.duckduckgo.com/html/?q={query}")
            if response.status_code != 200:
                return _mock_competitors(keyword, limit)

            soup = BeautifulSoup(response.text, "lxml")
            results = soup.select(".result")[:limit]
            for idx, result in enumerate(results, start=1):
                link = result.select_one("a.result__a")
                snippet = result.select_one(".result__snippet")
                if not link:
                    continue
                url = link.get("href", "")
                title = link.get_text(strip=True)
                competitors.append(
                    {
                        "position": idx,
                        "url": url,
                        "domain": _extract_domain(url),
                        "title": title,
                        "snippet": snippet.get_text(strip=True) if snippet else "",
                        "word_count": len(snippet.get_text().split()) * 20 if snippet else 0,
                        "has_faq": "faq" in (snippet.get_text().lower() if snippet else ""),
                    }
                )
    except httpx.HTTPError:
        return _mock_competitors(keyword, limit)

    if not competitors:
        return _mock_competitors(keyword, limit)
    return competitors


def _extract_domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else url


def _mock_competitors(keyword: str, limit: int) -> list[dict[str, Any]]:
    base = keyword.lower().replace(" ", "-")
    return [
        {
            "position": i,
            "url": f"https://competitor{i}.example.com/{base}",
            "domain": f"competitor{i}.example.com",
            "title": f"{keyword.title()} - Competitor {i}",
            "snippet": f"Top ranking page for {keyword} with comprehensive service details and FAQs.",
            "word_count": 900 - (i * 50),
            "has_faq": i <= 3,
        }
        for i in range(1, limit + 1)
    ]


def compare_page_with_serp(user_page: dict[str, Any] | None, competitors: list[dict[str, Any]]) -> dict[str, Any]:
    content_gaps: list[str] = []
    recommendations: list[str] = []

    if not user_page:
        content_gaps.append("No target page mapped for this keyword")
        recommendations.append("Create or assign a landing page for this keyword")
        return {"content_gaps": content_gaps, "recommendations": recommendations}

    avg_word_count = sum(c.get("word_count", 0) for c in competitors) / max(len(competitors), 1)
    if user_page.get("word_count", 0) < avg_word_count * 0.7:
        content_gaps.append("Content depth is below top-ranking pages")
        recommendations.append("Expand content with route details, pricing, FAQs, and trust signals")

    competitor_faq_ratio = sum(1 for c in competitors if c.get("has_faq")) / max(len(competitors), 1)
    if competitor_faq_ratio > 0.5 and not user_page.get("has_schema"):
        content_gaps.append("Competitors use FAQ/schema enhancements")
        recommendations.append("Add FAQ section with FAQ schema markup")

    if not user_page.get("meta_description"):
        recommendations.append("Write a compelling meta description to improve CTR")

    if user_page.get("internal_links_in", 0) < 2:
        recommendations.append("Strengthen internal links from related pages")

    if not user_page.get("h1"):
        recommendations.append("Add a clear H1 aligned with the target keyword")

    top_titles = [c.get("title", "") for c in competitors[:3]]
    if user_page.get("title") and all(user_page["title"].lower() not in t.lower() for t in top_titles):
        recommendations.append("Refresh title tag to better match high-ranking SERP patterns")

    return {"content_gaps": content_gaps, "recommendations": recommendations}
