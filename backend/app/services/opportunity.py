from __future__ import annotations

from app.models import CrawlIssue, GscMetric, Keyword, Page, RankHistory, SeoOpportunity, Severity


def position_segment(position: float | None) -> str:
    if position is None:
        return "not_ranking"
    if position <= 3:
        return "1-3"
    if position <= 10:
        return "4-10"
    if position <= 20:
        return "11-20"
    if position <= 50:
        return "21-50"
    return "51+"


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
) -> tuple[float, dict]:
    ranking_opportunity = 0.0
    if position is not None:
        if 4 <= position <= 20:
            ranking_opportunity = 90 - (position * 2)
        elif 21 <= position <= 50:
            ranking_opportunity = 50
        elif position > 50:
            ranking_opportunity = 25
        else:
            ranking_opportunity = max(0, 30 - position * 3)

    search_demand = min(100, impressions / 10) if impressions else 10
    ctr_opportunity = max(0, 5 - ctr) * 15 if impressions > 50 else 0

    signals = {
        "ranking_opportunity": round(ranking_opportunity, 1),
        "search_demand": round(search_demand, 1),
        "content_gap": round(content_gap, 1),
        "backlink_gap": round(backlink_gap, 1),
        "technical_impact": round(technical_impact, 1),
        "ctr_opportunity": round(ctr_opportunity, 1),
        "internal_link_opportunity": round(internal_link_gap, 1),
        "competitor_weakness": round(competitor_weakness, 1),
        "business_value": round(business_value, 1),
    }
    weights = {
        "ranking_opportunity": 0.35,
        "search_demand": 0.08,
        "content_gap": 0.12,
        "backlink_gap": 0.08,
        "technical_impact": 0.12,
        "ctr_opportunity": 0.08,
        "internal_link_opportunity": 0.07,
        "competitor_weakness": 0.05,
        "business_value": 0.05,
    }
    score = sum(signals[k] * weights[k] for k in weights)
    return round(min(100, score), 1), signals


def build_opportunities(
    keywords: list[Keyword],
    rank_map: dict[int, float | None],
    gsc_map: dict[str, GscMetric],
    pages: list[Page],
    issues_by_page: dict[int, list[CrawlIssue]],
) -> list[SeoOpportunity]:
    opportunities: list[SeoOpportunity] = []
    page_lookup = {p.id: p for p in pages}

    for keyword in keywords:
        position = rank_map.get(keyword.id)
        gsc = gsc_map.get(keyword.query.lower())
        page = page_lookup.get(keyword.target_page_id) if keyword.target_page_id else None
        page_issues = issues_by_page.get(page.id, []) if page else []
        technical_impact = min(100, len(page_issues) * 12)
        internal_link_gap = 70 if page and page.internal_links_in < 2 else 20
        content_gap = 60 if page and page.word_count < 400 else 25
        business_value = 80 if page and any(k in page.path.lower() for k in ("cab", "booking", "service")) else 40

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
        )

        if score < 20:
            continue

        segment = position_segment(position)
        title = f"Improve '{keyword.query}' ({segment})"
        evidence_parts = [
            f"Current position: {position if position else 'not ranking'}",
            f"Search demand signal: {signals['search_demand']}",
        ]
        if gsc:
            evidence_parts.append(f"GSC impressions: {gsc.impressions}, CTR: {gsc.ctr:.2%}")

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
    latest = history[0].position
    previous = history[1].position
    if latest is None or previous is None:
        return "new"
    delta = previous - latest
    if delta > 1:
        return "improved"
    if delta < -1:
        return "declined"
    return "stable"
