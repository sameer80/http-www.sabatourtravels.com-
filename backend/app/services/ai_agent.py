from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    AiConversation,
    AiMessage,
    CrawlIssue,
    CrawlRun,
    Keyword,
    Page,
    RankHistory,
    SeoOpportunity,
    SeoTask,
    Severity,
    TaskStatus,
    Website,
)
from app.services.audit import recommend_internal_links
from app.services.opportunity import position_segment


SYSTEM_PROMPT = """You are an AI SEO Manager. You analyze website crawl data, rankings, technical issues,
competitors, backlinks, and opportunities. You never guarantee #1 Google rankings. You always explain
evidence behind recommendations and prioritize by expected impact, effort, and business value.
When asked to create tasks or plans, be specific about page, keyword, and reason."""


class AiSeoAgent:
    def __init__(self, db: AsyncSession, website: Website):
        self.db = db
        self.website = website
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def gather_context(self) -> dict[str, Any]:
        pages_result = await self.db.execute(select(Page).where(Page.website_id == self.website.id))
        pages = pages_result.scalars().all()

        keywords_result = await self.db.execute(select(Keyword).where(Keyword.website_id == self.website.id))
        keywords = keywords_result.scalars().all()

        issues_result = await self.db.execute(
            select(CrawlIssue)
            .join(CrawlRun, CrawlIssue.crawl_run_id == CrawlRun.id)
            .where(CrawlRun.website_id == self.website.id)
            .limit(30)
        )
        issues = issues_result.scalars().all()

        opps_result = await self.db.execute(
            select(SeoOpportunity)
            .where(SeoOpportunity.website_id == self.website.id)
            .order_by(SeoOpportunity.score.desc())
            .limit(10)
        )
        opportunities = opps_result.scalars().all()

        rank_data = []
        for keyword in keywords[:20]:
            rh_result = await self.db.execute(
                select(RankHistory)
                .where(RankHistory.keyword_id == keyword.id)
                .order_by(RankHistory.recorded_at.desc())
                .limit(2)
            )
            history = rh_result.scalars().all()
            latest = history[0].position if history else None
            rank_data.append(
                {
                    "keyword": keyword.query,
                    "position": latest,
                    "segment": position_segment(latest),
                }
            )

        return {
            "website": {
                "name": self.website.name,
                "domain": self.website.domain,
                "base_url": self.website.base_url,
            },
            "pages_count": len(pages),
            "top_pages": [
                {
                    "path": p.path,
                    "title": p.title,
                    "word_count": p.word_count,
                    "internal_links_in": p.internal_links_in,
                    "is_orphan": p.is_orphan,
                }
                for p in sorted(pages, key=lambda x: x.internal_links_in, reverse=True)[:10]
            ],
            "keywords": rank_data,
            "issues": [
                {
                    "severity": i.severity.value,
                    "type": i.issue_type,
                    "message": i.message,
                }
                for i in issues
            ],
            "opportunities": [
                {
                    "title": o.title,
                    "score": o.score,
                    "evidence": o.evidence,
                }
                for o in opportunities
            ],
            "internal_link_recommendations": recommend_internal_links(pages, limit=5),
        }

    async def respond(self, user_message: str) -> tuple[str, dict[str, Any], list[SeoTask]]:
        context = await self.gather_context()
        evidence = {"context_summary": context}
        tasks: list[SeoTask] = []

        if self.client:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Project context:\n{json.dumps(context, indent=2)}\n\n"
                            f"User question:\n{user_message}"
                        ),
                    },
                ],
                temperature=0.3,
            )
            reply = response.choices[0].message.content or ""
        else:
            reply = self._rules_based_response(user_message.lower(), context)

        if any(phrase in user_message.lower() for phrase in ("create task", "fix today", "action plan", "30-day", "priorit")):
            tasks = await self._create_tasks_from_context(context)

        return reply, evidence, tasks

    def _rules_based_response(self, message: str, context: dict[str, Any]) -> str:
        if "audit" in message or "technical" in message:
            issues = context.get("issues", [])
            if not issues:
                return (
                    "I don't see technical issues yet. Run a website crawl first, then I can produce "
                    "a prioritized technical audit with severity levels."
                )
            critical = [i for i in issues if i["severity"] in ("critical", "high")]
            lines = [f"Technical audit for {context['website']['domain']}:", f"- Total issues sampled: {len(issues)}"]
            for issue in critical[:8]:
                lines.append(f"- [{issue['severity'].upper()}] {issue['message']}")
            lines.append("Evidence: findings are based on the latest crawl issue report.")
            return "\n".join(lines)

        if "rank" in message and ("drop" in message or "declin" in message):
            declining = [k for k in context.get("keywords", []) if k.get("segment") in ("21-50", "51+", "not_ranking")]
            if declining:
                names = ", ".join(k["keyword"] for k in declining[:5])
                return (
                    f"Keywords needing attention: {names}. I recommend checking recent technical changes, "
                    "content freshness, internal links, and competitor SERP updates. Evidence: current rank segments "
                    "from stored rank history."
                )
            return "No major declining keywords detected in stored rank history. Upload GSC data or add keywords to track movement."

        if "11" in message and "30" in message:
            matches = [
                k for k in context.get("keywords", [])
                if k.get("position") and 11 <= k["position"] <= 30
            ]
            if matches:
                return "Pages/keywords in positions 11-30:\n" + "\n".join(
                    f"- {k['keyword']}: position {k['position']}" for k in matches
                )
            return "No keywords currently tracked in positions 11-30. Add keywords and ranking data to monitor this segment."

        if "top 10" in message or "reach" in message:
            opps = context.get("opportunities", [])[:5]
            if opps:
                return (
                    "Highest-probability top-10 opportunities based on opportunity score:\n"
                    + "\n".join(f"- {o['title']} (score {o['score']}): {o['evidence']}" for o in opps)
                )
            return "Run a crawl, add keywords, and refresh opportunity scores to identify top-10 potential wins."

        if "backlink" in message:
            return (
                "Backlink opportunities require a connected backlink provider. Once connected, I can compare "
                "competitor referring domains and surface gap opportunities such as directories, citations, and editorial mentions."
            )

        if "internal link" in message:
            recs = context.get("internal_link_recommendations", [])
            if recs:
                return "Internal link recommendations:\n" + "\n".join(
                    f"- Link from {r['source_page']} to {r['target_page']} using anchor '{r['anchor_text']}' ({r['reason']})"
                    for r in recs
                )
            return "Crawl the website first so I can map the internal link graph and orphan pages."

        if "today" in message or "fix" in message:
            opps = context.get("opportunities", [])[:3]
            issues = [i for i in context.get("issues", []) if i["severity"] in ("critical", "high")][:3]
            lines = ["Here is what I would prioritize today:"]
            for issue in issues:
                lines.append(f"- Fix: {issue['message']} (severity: {issue['severity']})")
            for opp in opps:
                lines.append(f"- Opportunity: {opp['title']} — {opp['evidence']}")
            return "\n".join(lines) if len(lines) > 1 else "Add a website, run a crawl, and track keywords to get daily priorities."

        if "report" in message:
            return (
                f"SEO summary for {context['website']['name']}:\n"
                f"- Pages crawled: {context['pages_count']}\n"
                f"- Keywords tracked: {len(context.get('keywords', []))}\n"
                f"- Open opportunities: {len(context.get('opportunities', []))}\n"
                "Use the Reports screen to export HTML/PDF for management."
            )

        return (
            "I can help audit your website, diagnose ranking changes, find keywords in positions 11-30, "
            "compare pages against SERP competitors, suggest backlinks and internal links, and create prioritized tasks. "
            "Ask me something like: 'Audit my website', 'What should I fix today?', or 'Find keywords where I can reach the top 10'."
        )

    async def _create_tasks_from_context(self, context: dict[str, Any]) -> list[SeoTask]:
        created: list[SeoTask] = []
        issues = [i for i in context.get("issues", []) if i["severity"] in ("critical", "high")][:3]
        for issue in issues:
            task = SeoTask(
                website_id=self.website.id,
                priority=Severity.HIGH if issue["severity"] == "critical" else Severity.MEDIUM,
                title=f"Resolve: {issue['type'].replace('_', ' ')}",
                description=issue["message"],
                reason="Technical SEO issue detected during crawl",
                owner="Developer" if "404" in issue["type"] or "redirect" in issue["type"] else "SEO",
                status=TaskStatus.PENDING,
            )
            self.db.add(task)
            created.append(task)

        for opp in context.get("opportunities", [])[:3]:
            task = SeoTask(
                website_id=self.website.id,
                priority=Severity.HIGH,
                title=opp["title"],
                description=opp.get("evidence"),
                reason="High opportunity score",
                owner="SEO",
                status=TaskStatus.PENDING,
            )
            self.db.add(task)
            created.append(task)

        if created:
            await self.db.commit()
            for task in created:
                await self.db.refresh(task)
        return created

    async def save_conversation(
        self,
        user_id: int,
        user_message: str,
        reply: str,
        evidence: dict[str, Any],
        conversation_id: int | None,
    ) -> AiConversation:
        if conversation_id:
            result = await self.db.execute(
                select(AiConversation).where(
                    AiConversation.id == conversation_id,
                    AiConversation.website_id == self.website.id,
                )
            )
            conversation = result.scalar_one()
        else:
            conversation = AiConversation(
                website_id=self.website.id,
                user_id=user_id,
                title=user_message[:80],
            )
            self.db.add(conversation)
            await self.db.flush()

        self.db.add(AiMessage(conversation_id=conversation.id, role="user", content=user_message))
        self.db.add(
            AiMessage(conversation_id=conversation.id, role="assistant", content=reply, evidence=evidence)
        )
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
