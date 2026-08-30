"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

function SerpContent() {
  const { website } = useWebsite();
  const [keyword, setKeyword] = useState("Pune to Mumbai cab");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    if (!website) return;
    setLoading(true);
    setResult(await api.serpAnalysis(website.id, keyword));
    setLoading(false);
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">SERP Analysis</h2>
        <WebsiteSelector />
      </div>
      <form onSubmit={analyze} className="card flex gap-3">
        <input className="input" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
        <button className="btn" disabled={loading}>{loading ? "Analyzing..." : "Analyze"}</button>
      </form>
      {result && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card">
            <h3 className="mb-2 font-semibold">Competitor snapshot</h3>
            {result.competitors?.map((c: any) => (
              <div key={c.url} className="mb-2 rounded bg-slate-800 p-2 text-sm">
                <p>#{c.position} {c.title}</p>
                <p className="text-slate-400">{c.domain}</p>
              </div>
            ))}
          </div>
          <div className="card space-y-3">
            <div>
              <h3 className="font-semibold">Content gaps</h3>
              <ul className="list-disc pl-5 text-sm text-slate-300">
                {result.content_gaps?.map((g: string) => <li key={g}>{g}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold">Recommendations</h3>
              <ul className="list-disc pl-5 text-sm text-slate-300">
                {result.recommendations?.map((r: string) => <li key={r}>{r}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SerpPage() {
  return <SerpContent />;
}
