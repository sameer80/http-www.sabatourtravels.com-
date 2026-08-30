"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function ReportsContent() {
  const { website } = useWebsite();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!website) return;
    setLoading(true);
    api.dailyReport(website.id).then(setReport).finally(() => setLoading(false));
  }, [website]);

  if (!website) return <OnboardingCard />;
  if (loading || !report) return <p>Generating daily report...</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Daily SEO Report</h2>
          <p className="text-slate-400">{report.website.domain} — {new Date(report.generated_at).toLocaleString()}</p>
        </div>
        <WebsiteSelector />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {Object.entries(report.summary).map(([key, value]) => (
          <div key={key} className="card">
            <p className="text-sm capitalize text-slate-400">{key.replace(/_/g, " ")}</p>
            <p className="text-2xl font-bold">{value as number}</p>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 className="mb-3 font-semibold">Keyword movements</h3>
        <div className="space-y-3">
          {report.keyword_movements.map((row: any) => (
            <div key={row.keyword} className="rounded-lg bg-slate-800/80 p-3 text-sm">
              <p className="font-medium">{row.keyword}</p>
              <p className="text-slate-400">
                {row.previous_position ?? "—"} → {row.current_position ?? "—"}
                {row.change != null ? ` (${row.change > 0 ? "+" : ""}${row.change})` : ""} — {row.status}
              </p>
              <p className="mt-1 text-xs text-brand-400">{row.priority_zone}</p>
              <p className="mt-1 text-slate-300">{row.priority_action}</p>
              <p className="mt-1 text-xs text-slate-500">Owner: {row.owner} · {row.validation}</p>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-slate-500">{report.workflow_note}</p>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <WebsiteProvider>
      <ReportsContent />
    </WebsiteProvider>
  );
}
