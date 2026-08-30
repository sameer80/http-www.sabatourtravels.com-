"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

export default function DashboardPage() {
  const { website, websiteId, loading } = useWebsite();
  const [data, setData] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [crawling, setCrawling] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);

  useEffect(() => {
    api.portfolioOverview().then(setPortfolio).catch(() => {});
  }, []);

  useEffect(() => {
    if (!websiteId) {
      setData(null);
      return;
    }
    setDataLoading(true);
    api.dashboard(websiteId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setDataLoading(false));
  }, [websiteId]);

  async function runCrawl() {
    if (!website) return;
    setCrawling(true);
    await api.startCrawl(website.id);
    setTimeout(async () => {
      setData(await api.dashboard(website.id));
      setPortfolio(await api.portfolioOverview());
      setCrawling(false);
    }, 4000);
  }

  if (loading) return <p className="text-sm text-slate-400">Loading project...</p>;
  if (!website) return <OnboardingCard />;
  if (!data && dataLoading) return <p className="text-sm text-slate-400">Loading dashboard...</p>;
  if (!data) return <p className="text-sm text-slate-400">Could not load dashboard data.</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">SEO Dashboard</h2>
          <p className="text-slate-400">{data.website.domain} - {data.website.positioning || "Saba Tours portfolio"}</p>
        </div>
        <div className="flex gap-2">
          <WebsiteSelector />
          <button className="btn" onClick={runCrawl} disabled={crawling}>
            {crawling ? "Crawling..." : "Run crawl"}
          </button>
        </div>
      </div>

      {portfolio?.site_summaries?.length ? (
        <div className="card">
          <h3 className="mb-3 font-semibold">Portfolio - Saba Tours & Travels</h3>
          <div className="grid gap-3 md:grid-cols-3">
            {portfolio.site_summaries.map((site: any) => (
              <div key={site.website_id} className="rounded-lg bg-slate-800/80 p-3">
                <p className="font-medium">{site.name}</p>
                <p className="text-xs text-slate-400">{site.domain}</p>
                <div className="mt-2 grid grid-cols-2 gap-1 text-xs">
                  <span>SEO score</span><span className="text-right font-semibold">{site.seo_score}</span>
                  <span>Top 10</span><span className="text-right">{site.keywords_top_10}</span>
                  <span>High opp.</span><span className="text-right">{site.keywords_high_opportunity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {[
          ["SEO score", data.seo_score],
          ["Top 3 keywords", data.keywords_top_3],
          ["Top 10 keywords", data.keywords_top_10],
          ["Top 20 keywords", data.keywords_top_20],
          ["High opportunity (11-30)", data.keywords_high_opportunity],
        ].map(([label, value]) => (
          <div key={label as string} className="card">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-3xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ["Pages crawled", data.total_pages],
          ["Technical issues", data.total_issues],
          ["Keywords tracked", data.total_keywords],
          ["Open SEO tasks", data.pending_tasks],
        ].map(([label, value]) => (
          <div key={label as string} className="card">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold">AI recommendations</h3>
          <div className="space-y-2">
            {data.top_opportunities?.length ? data.top_opportunities.map((o: any) => (
              <div key={o.id} className="rounded-lg bg-slate-800/80 p-3">
                <div className="flex justify-between gap-2">
                  <p className="font-medium">{o.title}</p>
                  <span className="badge bg-brand-700">{o.score}</span>
                </div>
                <p className="text-xs text-slate-400">{o.evidence}</p>
              </div>
            )) : <p className="text-sm text-slate-400">Setup portfolio keywords or run a crawl to generate recommendations.</p>}
          </div>
        </div>
        <div className="card">
          <h3 className="mb-3 font-semibold">Technical issue severity</h3>
          <div className="space-y-2">
            {Object.entries(data.issues_by_severity || {}).map(([severity, count]) => (
              <div key={severity} className="flex justify-between rounded-lg bg-slate-800/80 px-3 py-2">
                <span className="capitalize">{severity}</span>
                <span>{count as number}</span>
              </div>
            ))}
            {!Object.keys(data.issues_by_severity || {}).length && (
              <p className="text-sm text-slate-400">No issues yet. Start with a website crawl.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
