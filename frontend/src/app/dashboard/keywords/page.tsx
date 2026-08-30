"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

function KeywordsContent() {
  const { website } = useWebsite();
  const [keywords, setKeywords] = useState<any[]>([]);
  const [query, setQuery] = useState("Pune to Mumbai cab");
  const [position, setPosition] = useState("12");

  async function refresh() {
    if (!website) return;
    setKeywords(await api.keywords(website.id));
  }

  useEffect(() => { refresh(); }, [website]);

  async function addKeyword(e: React.FormEvent) {
    e.preventDefault();
    if (!website) return;
    await api.addKeyword(website.id, { query, position: Number(position), country: "IN", city: "Pune" });
    setQuery("");
    refresh();
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Keywords & Rank Tracker</h2>
        <WebsiteSelector />
      </div>
      <form onSubmit={addKeyword} className="card grid gap-3 md:grid-cols-4">
        <input className="input md:col-span-2" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Keyword" />
        <input className="input" value={position} onChange={(e) => setPosition(e.target.value)} placeholder="Position" />
        <button className="btn">Add keyword</button>
      </form>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr><th>Keyword</th><th>Position</th><th>Movement</th><th>Location</th></tr>
          </thead>
          <tbody>
            {keywords.map((k) => (
              <tr key={k.id} className="border-t border-slate-800">
                <td className="py-2">{k.query}</td>
                <td className="py-2">{k.latest_position ?? "-"}</td>
                <td className="py-2 capitalize">{k.position_change ?? "stable"}</td>
                <td className="py-2">{k.city || k.country}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function KeywordsPage() {
  return <KeywordsContent />;
}
