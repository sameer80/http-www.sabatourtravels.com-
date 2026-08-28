"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function OverviewContent() {
  const { website } = useWebsite();
  const [data, setData] = useState<any>(null);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    if (!website) return;
    api.dashboard(website.id).then(setData);
  }, [website]);

  async function runCrawl() {
    if (!website) return;
    setCrawling(true);
    await api.startCrawl(website.id);
    setTimeout(async () => {
      setData(await api.dashboard(website.id));
      setCrawling(false);
    }, 4000);
  }

  if (!website) return <OnboardingCard />;
  if (!data) return <p>Loading dashboard...</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">SEO Overview</h2>
          <p className="text-slate-400">{data.website.domain}</p>
        </div>
        <div className="flex gap-2">
          <WebsiteSelector />
          <button className="btn" onClick={runCrawl} disabled={crawling}>
            {crawling ? "Crawling..." : "Run crawl"}
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ["Pages crawled", data.total_pages],
          ["Technical issues", data.total_issues],
          ["Keywords tracked", data.total_keywords],
          ["Pending tasks", data.pending_tasks],
        ].map(([label, value]) => (
          <div key={label as string} className="card">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-3xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold">Top opportunities</h3>
          <div className="space-y-2">
            {data.top_opportunities?.length ? data.top_opportunities.map((o: any) => (
              <div key={o.id} className="rounded-lg bg-slate-800/80 p-3">
                <div className="flex justify-between gap-2">
                  <p className="font-medium">{o.title}</p>
                  <span className="badge bg-brand-700">{o.score}</span>
                </div>
                <p className="text-xs text-slate-400">{o.evidence}</p>
              </div>
            )) : <p className="text-sm text-slate-400">Run a crawl and add keywords to generate opportunities.</p>}
          </div>
        </div>
        <div className="card">
          <h3 className="mb-3 font-semibold">Issue severity</h3>
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

export default function DashboardPage() {
  return (
    <WebsiteProvider>
      <OverviewContent />
    </WebsiteProvider>
  );
}
