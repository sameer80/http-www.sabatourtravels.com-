"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function RankingsContent() {
  const { website } = useWebsite();
  const [keywords, setKeywords] = useState<any[]>([]);

  useEffect(() => {
    if (!website) return;
    api.keywords(website.id).then(setKeywords);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Rankings</h2>
          <p className="text-slate-400">Keyword positions with SRS priority zones (Protect / Top 10 / High / Medium / Low)</p>
        </div>
        <WebsiteSelector />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-4">Keyword</th>
              <th className="pb-2 pr-4">Position</th>
              <th className="pb-2 pr-4">Change</th>
              <th className="pb-2 pr-4">Zone</th>
              <th className="pb-2 pr-4">Volume</th>
              <th className="pb-2">KD</th>
            </tr>
          </thead>
          <tbody>
            {keywords.map((k) => (
              <tr key={k.id} className="border-t border-slate-800">
                <td className="py-3 pr-4">{k.query}</td>
                <td className="py-3 pr-4">{k.latest_position ?? "—"}</td>
                <td className="py-3 pr-4">
                  {k.position_change != null ? (
                    <span className={k.position_change > 0 ? "text-green-400" : k.position_change < 0 ? "text-red-400" : ""}>
                      {k.position_change > 0 ? "+" : ""}{k.position_change}
                    </span>
                  ) : k.position_trend || "—"}
                </td>
                <td className="py-3 pr-4"><span className="badge bg-slate-700">{k.priority_zone || "—"}</span></td>
                <td className="py-3 pr-4">{k.search_volume ?? "—"}</td>
                <td className="py-3">{k.keyword_difficulty ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!keywords.length && <p className="py-4 text-sm text-slate-400">No keywords yet. Setup the Saba Tours portfolio from the dashboard.</p>}
      </div>
    </div>
  );
}

export default function RankingsPage() {
  return (
    <WebsiteProvider>
      <RankingsContent />
    </WebsiteProvider>
  );
}
