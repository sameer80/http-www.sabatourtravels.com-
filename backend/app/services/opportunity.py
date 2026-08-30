from __future__ import annotations

from app.models import CrawlIssue, GscMetric, Keyword, Page, RankHistory, SeoOpportunity, Severity

# SRS section 8 — keyword opportunity zones
PRIORITY_ZONES = {
    "protect": {"label": "PROTECT", "range": (1, 3), "score_boost": 15},
    "top_10": {"label": "TOP 10 OPPORTUNITY", "range": (4, 10), "score_boost": 70},
    "high": {"label": "HIGH OPPORTUNITY", "range": (11, 30), "score_boost": 95},
    "medium": {"label": "MEDIUM OPPORTUNITY", "range": (31, 50), "score_boost": 55},
    "low": {"label": "LOW/STRATEGIC", "range": (51, 100), "score_boost": 25},
}


def position_priority_zone(position: float | None) -> str:
    if position is None:
        return "not_ranking"
    if position <= 3:
        return "protect"
    if position <= 10:
        return "top_10"
    if position <= 30:
        return "high"
    if position <= 50:
        return "medium"
    if position <= 100:
        return "low"
    return "not_ranking"


def position_segment(position: float | None) -> str:
    zone = position_priority_zone(position)
    if zone == "not_ranking":
        return "not_ranking"
    low, high = PRIORITY_ZONES[zone]["range"]
    return f"{low}-{high}"


def zone_label(position: float | None) -> str:
    zone = position_priority_zone(position)
    if zone == "not_ranking":
        return "NOT RANKING"
    return PRIORITY_ZONES[zone]["label"]


def compute_opportunity_score(
    *,
    position: float | None,
    impressions: int,
    ctr: float,
    content_gap: float,
    backlink_gap: float,
    technical_impact: float,
    internal_link_gap: float,
    competitor_weakness: float,
    business_value: float,
    search_volume: int = 0,
    keyword_difficulty: float = 0,
) -> tuple[float, dict]:
    zone = position_priority_zone(position)
    ranking_opportunity = 0.0
    if zone in PRIORITY_ZONES:
        ranking_opportunity = float(PRIORITY_ZONES[zone]["score_boost"])
        if zone == "high" and position is not None:
            ranking_opportunity += max(0, 30 - (position - 11))
        elif zone == "top_10" and position is not None:
            ranking_opportunity += max(0, 15 - (position - 4))
    elif position is None:
        ranking_opportunity = 40

    search_demand = min(100, (impressions / 10) if impressions else (search_volume / 50 if search_volume else 10))
    difficulty_penalty = min(30, keyword_difficulty * 0.3) if keyword_difficulty else 0
    ctr_opportunity = max(0, 5 - ctr) * 15 if impressions > 50 else 0

    signals = {
        "priority_zone": zone_label(position),
        "ranking_opportunity": round(ranking_opportunity, 1),
        "search_demand": round(search_demand, 1),
        "content_gap": round(content_gap, 1),
        "backlink_gap": round(backlink_gap, 1),
        "technical_impact": round(technical_impact, 1),
        "ctr_opportunity": round(ctr_opportunity, 1),
        "internal_link_opportunity": round(internal_link_gap, 1),
        "competitor_weakness": round(competitor_weakness, 1),
        "business_value": round(business_value, 1),
        "keyword_difficulty_penalty": round(difficulty_penalty, 1),
    }
    weights = {
        "ranking_opportunity": 0.35,
        "search_demand": 0.10,
        "content_gap": 0.12,
        "backlink_gap": 0.08,
        "technical_impact": 0.12,
        "ctr_opportunity": 0.06,
        "internal_link_opportunity": 0.07,
        "competitor_weakness": 0.05,
        "business_value": 0.05,
    }
    score = sum(signals[k] * weights[k] for k in weights) - difficulty_penalty * 0.15
    return round(min(100, max(0, score)), 1), signals


def build_opportunities(
    keywords: list[Keyword],
    rank_map: dict[int, float | None],
    rank_meta: dict[int, dict],
    gsc_map: dict[str, GscMetric],
    pages: list[Page],
    issues_by_page: dict[int, list[CrawlIssue]],
) -> list[SeoOpportunity]:
    opportunities: list[SeoOpportunity] = []
    page_lookup = {p.id: p for p in pages}

    for keyword in keywords:
        position = rank_map.get(keyword.id)
        meta = rank_meta.get(keyword.id, {})
        gsc = gsc_map.get(keyword.query.lower())
        page = page_lookup.get(keyword.target_page_id) if keyword.target_page_id else None
        page_issues = issues_by_page.get(page.id, []) if page else []
        technical_impact = min(100, len(page_issues) * 12)
        internal_link_gap = 70 if page and page.internal_links_in < 2 else 20
        content_gap = 60 if page and page.word_count < 400 else 25
        business_value = 80 if page and any(k in page.path.lower() for k in ("cab", "booking", "service", "tour")) else 40

        score, signals = compute_opportunity_score(
            position=position,
            impressions=gsc.impressions if gsc else 0,
            ctr=gsc.ctr if gsc else 0,
            content_gap=content_gap,
            backlink_gap=35,
            technical_impact=technical_impact,
            internal_link_gap=internal_link_gap,
            competitor_weakness=30,
            business_value=business_value,
            search_volume=meta.get("search_volume", 0),
            keyword_difficulty=meta.get("keyword_difficulty", 0),
        )

        if score < 20 and position_priority_zone(position) not in ("protect", "high"):
            continue

        segment = position_segment(position)
        zone = zone_label(position)
        title = f"[{zone}] Improve '{keyword.query}' ({segment})"
        evidence_parts = [
            f"Current position: {position if position else 'not ranking'}",
            f"Priority zone: {zone}",
            f"Search demand signal: {signals['search_demand']}",
        ]
        if gsc:
            evidence_parts.append(f"GSC impressions: {gsc.impressions}, CTR: {gsc.ctr:.2%}")
        if meta.get("position_change") is not None:
            evidence_parts.append(f"Position change: {meta['position_change']:+.0f}")

        opportunities.append(
            SeoOpportunity(
                website_id=keyword.website_id,
                page_id=keyword.target_page_id,
                keyword_id=keyword.id,
                title=title,
                opportunity_type="ranking_improvement",
                score=score,
                signals=signals,
                evidence="; ".join(evidence_parts),
            )
        )

    for page in pages:
        page_issues = issues_by_page.get(page.id, [])
        critical = [i for i in page_issues if i.severity in (Severity.CRITICAL, Severity.HIGH)]
        if not critical:
            continue
        score, signals = compute_opportunity_score(
            position=None,
            impressions=0,
            ctr=0,
            content_gap=20,
            backlink_gap=10,
            technical_impact=min(100, len(critical) * 20),
            internal_link_gap=30 if page.is_orphan else 10,
            competitor_weakness=0,
            business_value=50,
        )
        opportunities.append(
            SeoOpportunity(
                website_id=page.website_id,
                page_id=page.id,
                keyword_id=None,
                title=f"Fix technical issues on {page.path}",
                opportunity_type="technical_seo",
                score=score,
                signals=signals,
                evidence=f"{len(critical)} high/critical issues detected",
            )
        )

    opportunities.sort(key=lambda o: o.score, reverse=True)
    return opportunities[:50]


def rank_change_label(history: list[RankHistory]) -> str | None:
    if len(history) < 2:
        return None
    latest = history[0]
    if latest.position_change is not None:
        if latest.position_change > 1:
            return "improved"
        if latest.position_change < -1:
            return "declined"
        return "stable"
    previous = history[1].position if len(history) > 1 else None
    curr = latest.position
    if curr is None or previous is None:
        return "new"
    delta = previous - curr
    if delta > 1:
        return "improved"
    if delta < -1:
        return "declined"
    return "stable"
