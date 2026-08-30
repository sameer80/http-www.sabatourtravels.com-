"""Cross-portfolio backlink plan for Saba Tours owned websites."""

from __future__ import annotations

from app.data.saba_tours_portfolio import SABA_TOURS_PORTFOLIO

# Anchor suggestions when linking between portfolio sites (same business, different domains).
CROSS_LINK_ANCHORS: dict[tuple[str, str], str] = {
    ("onewaydrop.cab", "sabacabs.com"): "Pune to Mumbai cab booking",
    ("onewaydrop.cab", "punetomumbaicabservice.com"): "Pune Mumbai cab service",
    ("sabacabs.com", "onewaydrop.cab"): "Pune to Mumbai one way cab",
    ("sabacabs.com", "punetomumbaicabservice.com"): "Pune to Mumbai cab service",
    ("punetomumbaicabservice.com", "onewaydrop.cab"): "One way cab Pune to Mumbai",
    ("punetomumbaicabservice.com", "sabacabs.com"): "Pune airport and outstation cabs",
}


def build_cross_link_plan() -> list[dict]:
    """Build dofollow cross-links between all portfolio domains (excluding self-links)."""
    plan: list[dict] = []

    for source in SABA_TOURS_PORTFOLIO:
        for target in SABA_TOURS_PORTFOLIO:
            if source.domain == target.domain:
                continue
            anchor = CROSS_LINK_ANCHORS.get(
                (source.domain, target.domain),
                f"{target.name} - {target.positioning}",
            )
            plan.append(
                {
                    "source_domain": source.domain,
                    "source_name": source.name,
                    "source_base_url": source.base_url,
                    "target_domain": target.domain,
                    "target_name": target.name,
                    "target_url": target.base_url.rstrip("/") + "/",
                    "anchor_text": anchor,
                    "html_snippet": (
                        f'<p><a href="{target.base_url.rstrip("/")}/" rel="noopener" '
                        f'target="_blank">{anchor}</a></p>'
                    ),
                    "post_to": "footer_or_partners_page",
                    "notes": f"Add on {source.domain} linking to {target.domain} (your own site).",
                }
            )
    return plan


def plan_for_domain(domain: str) -> list[dict]:
    domain = domain.lower().strip()
    return [item for item in build_cross_link_plan() if item["source_domain"] == domain]
