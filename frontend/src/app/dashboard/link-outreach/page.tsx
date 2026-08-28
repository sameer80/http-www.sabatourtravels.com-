"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function LinkOutreachContent() {
  const { website } = useWebsite();
  const [keyword, setKeyword] = useState("Pune to Mumbai cab");
  const [targetUrl, setTargetUrl] = useState("https://sabacabs.com/service/pune-mumbai-innova-cab-services");
  const [anchorText, setAnchorText] = useState("Pune to Mumbai cab booking");
  const [minDa, setMinDa] = useState("30");
  const [minPa, setMinPa] = useState("25");
  const [prospects, setProspects] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    if (!website) return;
    setProspects(await api.linkProspects(website.id, Number(minDa)));
  }

  useEffect(() => {
    refresh();
  }, [website]);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!website) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.searchLinkProspects(website.id, {
        keyword,
        target_url: targetUrl,
        anchor_text: anchorText,
        min_da: Number(minDa),
        min_pa: Number(minPa),
      });
      setProspects(res.prospects);
      setPlan(res.submission_plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function markPosted(id: number) {
    if (!website) return;
    const postedUrl = prompt("Paste the live URL where you posted your link (optional):") || undefined;
    const notes = prompt("Any notes about this submission?") || undefined;
    await api.updateLinkProspect(website.id, id, {
      outreach_status: "posted",
      posted_url: postedUrl,
      notes,
    });
    refresh();
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">High DA/PA Link Outreach</h2>
          <p className="text-sm text-slate-400">Search Google for high-authority sites, then post your URL with target keyword</p>
        </div>
        <WebsiteSelector />
      </div>

      <form onSubmit={search} className="card grid gap-3 md:grid-cols-2">
        <input className="input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Target keyword" />
        <input className="input" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} placeholder="Your URL to post" />
        <input className="input" value={anchorText} onChange={(e) => setAnchorText(e.target.value)} placeholder="Anchor text" />
        <div className="grid grid-cols-2 gap-2">
          <input className="input" value={minDa} onChange={(e) => setMinDa(e.target.value)} placeholder="Min DA" />
          <input className="input" value={minPa} onChange={(e) => setMinPa(e.target.value)} placeholder="Min PA" />
        </div>
        <button className="btn md:col-span-2" disabled={loading}>
          {loading ? "Searching Google..." : "Search high DA/PA prospects"}
        </button>
        {error && <p className="text-sm text-red-400 md:col-span-2">{error}</p>}
      </form>

      {plan && (
        <div className="card space-y-2 text-sm">
          <h3 className="font-semibold">Submission plan for your URL + keyword</h3>
          <p><span className="text-slate-400">Target URL:</span> {plan.target_url}</p>
          <p><span className="text-slate-400">Suggested anchor:</span> {plan.suggested_anchor}</p>
          <p><span className="text-slate-400">Title:</span> {plan.title_suggestion}</p>
          <p><span className="text-slate-400">Description:</span> {plan.description_suggestion}</p>
          <p className="text-slate-400">{plan.posting_tip}</p>
        </div>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th>DA</th>
              <th>PA</th>
              <th>PR</th>
              <th>Domain</th>
              <th>Type</th>
              <th>Keyword</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {prospects.map((p) => (
              <tr key={p.id} className="border-t border-slate-800">
                <td className="py-2 font-semibold text-brand-500">{Math.round(p.domain_authority)}</td>
                <td className="py-2">{Math.round(p.page_authority)}</td>
                <td className="py-2">{p.page_rank}</td>
                <td className="py-2">
                  <a href={p.prospect_url} target="_blank" rel="noreferrer" className="text-brand-500 hover:underline">
                    {p.prospect_domain}
                  </a>
                </td>
                <td className="py-2 capitalize">{p.prospect_type.replace("_", " ")}</td>
                <td className="py-2">{p.keyword}</td>
                <td className="py-2 capitalize">{p.outreach_status.replace("_", " ")}</td>
                <td className="py-2">
                  {p.outreach_status !== "posted" && p.outreach_status !== "live" && (
                    <button className="btn" onClick={() => markPosted(p.id)}>Mark posted</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!prospects.length && (
          <p className="text-sm text-slate-400">Search to find high DA/PA sites where you can post your URL with your keyword.</p>
        )}
      </div>
    </div>
  );
}

export default function LinkOutreachPage() {
  return (
    <WebsiteProvider>
      <LinkOutreachContent />
    </WebsiteProvider>
  );
}
