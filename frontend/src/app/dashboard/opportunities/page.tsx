"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function OpportunitiesContent() {
  const { website } = useWebsite();
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    if (!website) return;
    api.opportunities(website.id).then(setItems);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">SEO Opportunity Center</h2>
        <WebsiteSelector />
      </div>
      <div className="grid gap-4">
        {items.map((o) => (
          <div key={o.id} className="card">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-semibold">{o.title}</h3>
              <span className="badge bg-brand-700">Score {o.score}</span>
            </div>
            <p className="text-sm text-slate-300">{o.evidence}</p>
            {o.signals && (
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
                {Object.entries(o.signals).map(([k, v]) => (
                  <span key={k} className="rounded bg-slate-800 px-2 py-1">{k}: {v as number}</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {!items.length && <p className="text-slate-400">No opportunities yet. Crawl the site and add keywords first.</p>}
      </div>
    </div>
  );
}

export default function OpportunitiesPage() {
  return <WebsiteProvider><OpportunitiesContent /></WebsiteProvider>;
}
