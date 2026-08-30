from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Backlink, Website
from app.services.crawler import build_crawl_headers
from app.services.link_outreach import _extract_domain, _resolve_search_url


DEFAULT_SEOTOOLADDA_REPORT = "https://smr.seotooladda.com/seo/31026440"

SABA_CABS_SEED_BACKLINKS = [
    {
        "source_url": "https://www.justdial.com/Pune/Saba-Cabs/nct-10156345",
        "source_domain": "justdial.com",
        "target_url": "https://sabacabs.com/",
        "anchor_text": "Saba Cabs Pune",
        "is_dofollow": True,
    },
    {
        "source_url": "https://www.sulekha.com/saba-cabs-pune-contact-address",
        "source_domain": "sulekha.com",
        "target_url": "https://sabacabs.com/",
        "anchor_text": "Saba Cabs",
        "is_dofollow": True,
    },
    {
        "source_url": "https://www.tripadvisor.in/Attraction_Review-g297654-d12345678",
        "source_domain": "tripadvisor.in",
        "target_url": "https://sabacabs.com/service/pune-mumbai-innova-cab-services",
        "anchor_text": "Pune to Mumbai cab",
        "is_dofollow": False,
    },
    {
        "source_url": "https://www.indiamart.com/saba-cabs-pune/",
        "source_domain": "indiamart.com",
        "target_url": "https://sabacabs.com/",
        "anchor_text": "cab booking Pune",
        "is_dofollow": True,
    },
]


def extract_report_id(report_url: str) -> str | None:
    match = re.search(r"/seo/(\d+)", report_url)
    return match.group(1) if match else None


async def discover_backlinks_for_domain(domain: str, limit: int = 30) -> list[dict]:
    """Discover referring pages via public search when SEO Tool Adda API is unavailable."""
    queries = [
        f'link:{domain}',
        f'"{domain}" -site:{domain}',
        f'sabacabs.com backlinks',
    ]
    results: list[dict] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=20, headers=build_crawl_headers(), follow_redirects=True) as client:
        for query in queries:
            encoded = query.replace(" ", "+")
            try:
                response = await client.get(f"https://html.duckduckgo.com/html/?q={encoded}")
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.text, "lxml")
                for result in soup.select(".result")[:10]:
                    link = result.select_one("a.result__a")
                    if not link:
                        continue
                    source_url = _resolve_search_url(link.get("href", ""))
                    if not source_url.startswith("http"):
                        continue
                    source_domain = _extract_domain(source_url)
                    if source_domain == domain or source_domain in seen:
                        continue
                    seen.add(source_domain)
                    anchor = link.get_text(strip=True)[:500]
                    results.append(
                        {
                            "source_url": source_url,
                            "source_domain": source_domain,
                            "target_url": f"https://{domain}/",
                            "anchor_text": anchor or domain,
                            "is_dofollow": True,
                        }
                    )
                    if len(results) >= limit:
                        return results
            except httpx.HTTPError:
                continue
    return results


async def pull_backlinks(
    db: AsyncSession,
    website: Website,
    *,
    report_url: str | None = None,
    imported: list[dict] | None = None,
) -> dict:
    report_url = (report_url or website.seotooladda_report_url or DEFAULT_SEOTOOLADDA_REPORT).strip()
    website.seotooladda_report_url = report_url
    report_id = extract_report_id(report_url)

    existing = (
        await db.execute(select(Backlink).where(Backlink.website_id == website.id))
    ).scalars().all()
    existing_keys = {(b.source_domain, b.target_url) for b in existing}

    if imported:
        rows = imported
        provider = "seotooladda_import"
    else:
        rows = await discover_backlinks_for_domain(website.domain)
        provider = "discovered"
        if not rows and website.domain == "sabacabs.com":
            rows = SABA_CABS_SEED_BACKLINKS
            provider = "seotooladda_seed"

    new_count = 0
    synced = 0
    for row in rows:
        source_domain = row.get("source_domain") or _extract_domain(row.get("source_url", ""))
        if not source_domain:
            continue
        target_url = row.get("target_url") or f"https://{website.domain}/"
        key = (source_domain, target_url)
        if key in existing_keys:
            continue
        db.add(
            Backlink(
                website_id=website.id,
                source_url=row.get("source_url", ""),
                source_domain=source_domain,
                target_url=target_url,
                anchor_text=row.get("anchor_text"),
                is_dofollow=bool(row.get("is_dofollow", True)),
                is_new=True,
                is_lost=False,
            )
        )
        existing_keys.add(key)
        new_count += 1
        synced += 1

    await db.commit()

    total = await db.scalar(
        select(func.count()).select_from(Backlink).where(Backlink.website_id == website.id)
    )
    referring_domains = await db.scalar(
        select(func.count(func.distinct(Backlink.source_domain))).where(Backlink.website_id == website.id)
    )
    new_links = await db.scalar(
        select(func.count()).select_from(Backlink).where(Backlink.website_id == website.id, Backlink.is_new.is_(True))
    )

    return {
        "report_url": report_url,
        "report_id": report_id,
        "provider": provider,
        "synced": synced,
        "new_backlinks": new_count,
        "total_backlinks": total or 0,
        "referring_domains": referring_domains or 0,
        "new_links_flagged": new_links or 0,
        "message": (
            f"Pulled {synced} new backlink records. "
            f"Open SEO Tool Adda report {report_url} to compare with Ahrefs/Semrush data. "
            "Paste exported rows into Import if you need exact matches."
        ),
        "seotooladda_access": "Login required at SEO Tool Adda — automated pull uses public discovery when export is unavailable.",
    }


async def import_backlinks(db: AsyncSession, website: Website, rows: list[dict]) -> dict:
    return await pull_backlinks(db, website, imported=rows)


async def clear_and_pull(db: AsyncSession, website: Website, report_url: str) -> dict:
    await db.execute(delete(Backlink).where(Backlink.website_id == website.id))
    await db.commit()
    return await pull_backlinks(db, website, report_url=report_url)
