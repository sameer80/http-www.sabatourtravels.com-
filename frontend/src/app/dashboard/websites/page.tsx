"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider } from "@/components/WebsiteContext";

function WebsitesContent() {
  const { website } = useWebsite();
  const [portfolio, setPortfolio] = useState<any>(null);

  useEffect(() => {
    api.portfolioOverview().then(setPortfolio).catch(() => {});
  }, [website]);

  if (!website) return <OnboardingCard />;
  if (!portfolio) return <p>Loading websites...</p>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Websites</h2>
        <p className="text-slate-400">Three-domain SEO management for Saba Tours & Travels</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {portfolio.websites.map((site: any) => {
          const summary = portfolio.site_summaries.find((s: any) => s.website_id === site.id);
          return (
            <div key={site.id} className="card space-y-3">
              <div>
                <h3 className="text-lg font-semibold">{site.name}</h3>
                <p className="text-sm text-brand-400">{site.domain}</p>
              </div>
              <p className="text-sm text-slate-300">{site.positioning}</p>
              <p className="text-xs text-slate-400">{site.seo_focus}</p>
              {summary && (
                <div className="rounded-lg bg-slate-800/80 p-3 text-sm">
                  <div className="flex justify-between"><span>SEO score</span><strong>{summary.seo_score}</strong></div>
                  <div className="flex justify-between"><span>Keywords</span><span>{summary.keywords_top_10} in Top 10</span></div>
                  <div className="flex justify-between"><span>Issues</span><span>{summary.technical_issues}</span></div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function WebsitesPage() {
  return (
    <WebsiteProvider>
      <WebsitesContent />
    </WebsiteProvider>
  );
}
