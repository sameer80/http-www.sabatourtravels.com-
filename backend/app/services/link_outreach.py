from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.services.crawler import build_crawl_headers


OUTREACH_QUERIES = [
    "guest post {keyword}",
    "cab booking directory submit",
]

CURATED_PROSPECTS = [
    ("https://www.quora.com/search?q={q}", "quora.com", "forum", 80, 78, 8.0),
    ("https://medium.com/search?q={q}", "medium.com", "guest_post", 85, 82, 8.5),
    ("https://www.justdial.com/search?q={q}", "justdial.com", "directory", 72, 70, 7.2),
    ("https://www.tripadvisor.in/Search?q={q}", "tripadvisor.in", "citation", 88, 85, 8.8),
    ("https://www.indiamart.com/search.mp?ss={q}", "indiamart.com", "directory", 76, 74, 7.6),
    ("https://www.sulekha.com/cab-services/pune", "sulekha.com", "directory", 74, 72, 7.4),
    ("https://www.mouthshut.com/search/procedure/{q}", "mouthshut.com", "citation", 73, 71, 7.3),
]

HIGH_AUTHORITY_TLD_BONUS = {".edu": 25, ".gov": 30, ".org": 10}
KNOWN_HIGH_AUTHORITY = {
    "medium.com": 85,
    "linkedin.com": 90,
    "quora.com": 80,
    "reddit.com": 78,
    "wordpress.com": 75,
    "blogspot.com": 70,
    "wikipedia.org": 95,
    "indiatimes.com": 82,
    "justdial.com": 72,
    "tripadvisor.com": 88,
}


def _resolve_search_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    if raw_url.startswith("//"):
        raw_url = f"https:{raw_url}"
    parsed = urlparse(raw_url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return raw_url


def _extract_domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    if match:
        return match.group(1).lower().removeprefix("www.")
    return url.lower()


def _classify_prospect(url: str, title: str, snippet: str) -> str:
    text = f"{url} {title} {snippet}".lower()
    if any(k in text for k in ("write for us", "guest post", "contribute", "submit article")):
        return "guest_post"
    if any(k in text for k in ("directory", "add your site", "submit url", "listing")):
        return "directory"
    if any(k in text for k in ("forum", "discussion", "community")):
        return "forum"
    if any(k in text for k in ("resource", "citation", "reference")):
        return "citation"
    return "editorial"


def _estimate_authority(domain: str, serp_position: int) -> tuple[float, float, float]:
    domain = domain.lower().removeprefix("www.")
    base_da = KNOWN_HIGH_AUTHORITY.get(domain, 35)
    for tld, bonus in HIGH_AUTHORITY_TLD_BONUS.items():
        if domain.endswith(tld):
            base_da += bonus
            break
    if "blog" in domain:
        base_da += 5
    position_bonus = max(0, 15 - serp_position)
    da = min(100, base_da + position_bonus)
    pa = min(100, da - 5 + max(0, 8 - serp_position))
    pr = round(da / 10, 1)
    return da, pa, pr


async def fetch_openpagerank(domains: list[str]) -> dict[str, float]:
    if not domains:
        return {}
    unique = list(dict.fromkeys(domains))[:50]
    headers = build_crawl_headers()
    if settings.openpagerank_api_key:
        headers["API-OPR"] = settings.openpagerank_api_key
    try:
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            resp = await client.get(
                "https://openpagerank.com/api/v1.0/getPageRank",
                params={"domains[]": unique},
            )
            if resp.status_code != 200:
                return {}
            data = resp.json()
            scores: dict[str, float] = {}
            for item in data.get("response", []):
                domain = item.get("domain", "").lower()
                rank = float(item.get("page_rank_decimal") or item.get("page_rank_integer") or 0)
                if domain:
                    scores[domain] = rank
            return scores
    except httpx.HTTPError:
        return {}


async def search_google_prospects(keyword: str, limit_per_query: int = 5) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen_domains: set[str] = set()

    async with httpx.AsyncClient(timeout=20, headers=build_crawl_headers(), follow_redirects=True) as client:
        for template in OUTREACH_QUERIES:
            query = template.format(keyword=keyword)
            encoded = query.replace(" ", "+")
            try:
                response = await client.get(f"https://html.duckduckgo.com/html/?q={encoded}")
                if response.status_code != 200:
                    await asyncio.sleep(2)
                    continue
                soup = BeautifulSoup(response.text, "lxml")
                for idx, result in enumerate(soup.select(".result")[:limit_per_query], start=1):
                    link = result.select_one("a.result__a")
                    snippet_el = result.select_one(".result__snippet")
                    if not link:
                        continue
                    url = _resolve_search_url(link.get("href", ""))
                    if not url.startswith("http"):
                        continue
                    domain = _extract_domain(url)
                    if domain in seen_domains or "duckduckgo." in domain:
                        continue
                    seen_domains.add(domain)
                    title = link.get_text(strip=True)
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    da, pa, pr = _estimate_authority(domain, idx)
                    results.append(
                        {
                            "prospect_url": url,
                            "prospect_domain": domain,
                            "prospect_title": title,
                            "prospect_type": _classify_prospect(url, title, snippet),
                            "domain_authority": da,
                            "page_authority": pa,
                            "page_rank": pr,
                            "google_query": query,
                            "snippet": snippet,
                            "metrics_source": "google_search",
                        }
                    )
            except httpx.HTTPError:
                continue
            await asyncio.sleep(2)

    q = keyword.replace(" ", "+")
    for url, domain, ptype, da, pa, pr in CURATED_PROSPECTS:
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        results.append(
            {
                "prospect_url": url.format(q=q),
                "prospect_domain": domain,
                "prospect_title": f"{keyword} on {domain}",
                "prospect_type": ptype,
                "domain_authority": da,
                "page_authority": pa,
                "page_rank": pr,
                "google_query": f"curated {keyword}",
                "snippet": f"High-authority {ptype.replace('_', ' ')} opportunity for {keyword}",
                "metrics_source": "curated",
            }
        )

    opr_scores = await fetch_openpagerank([r["prospect_domain"] for r in results])
    for item in results:
        opr = opr_scores.get(item["prospect_domain"])
        if opr and opr > 0:
            item["page_rank"] = opr
            item["domain_authority"] = min(100, opr * 10)
            item["page_authority"] = min(100, item["domain_authority"] - 3)
            item["metrics_source"] = f"{item['metrics_source']}+openpagerank"

    results.sort(key=lambda x: (x["domain_authority"], x["page_authority"]), reverse=True)
    return results


def _fallback_prospects(keyword: str) -> list[dict[str, Any]]:
    """Deprecated: curated prospects are merged in search_google_prospects."""
    q = keyword.replace(" ", "+")
    return [
        {
            "prospect_url": url.format(q=q),
            "prospect_domain": domain,
            "prospect_title": f"{keyword} on {domain}",
            "prospect_type": ptype,
            "domain_authority": da,
            "page_authority": pa,
            "page_rank": pr,
            "google_query": f"curated {keyword}",
            "snippet": f"High-authority {ptype.replace('_', ' ')} opportunity for {keyword}",
            "metrics_source": "curated",
        }
        for url, domain, ptype, da, pa, pr in CURATED_PROSPECTS
    ]


def build_submission_plan(
    target_url: str,
    keyword: str,
    anchor_text: str | None = None,
    prospect_type: str = "editorial",
) -> dict[str, str]:
    anchor = anchor_text or keyword
    return {
        "target_url": target_url,
        "keyword": keyword,
        "suggested_anchor": anchor,
        "title_suggestion": f"{keyword.title()} | Saba Cabs",
        "description_suggestion": (
            f"Book reliable {keyword} with Saba Cabs. Safe, on-time cab service across Pune, Mumbai and outstation routes. "
            f"Visit {target_url}"
        ),
        "prospect_type": prospect_type,
        "posting_tip": (
            "Use natural anchor text, include your URL once, and match the page's submission guidelines. "
            "Avoid spammy exact-match anchors on low-quality directories."
        ),
    }
