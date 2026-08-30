"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

function ProspectLink({ url, label }: { url: string; label?: string }) {
  if (!url) return <span className="text-slate-500">—</span>;
  return (
    <a href={url} target="_blank" rel="noreferrer" className="table-link break-all">
      {label || url}
    </a>
  );
}

function LinkOutreachContent() {
  const { website, loading: websiteLoading } = useWebsite();
  const [keyword, setKeyword] = useState("Pune to Mumbai cab");
  const [targetUrl, setTargetUrl] = useState("https://sabacabs.com/service/pune-mumbai-innova-cab-services");
  const [anchorText, setAnchorText] = useState("Pune to Mumbai cab booking");
  const [minDa, setMinDa] = useState("30");
  const [minPa, setMinPa] = useState("25");
  const [prospects, setProspects] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [markingId, setMarkingId] = useState<number | null>(null);
  const [postedUrlInput, setPostedUrlInput] = useState("");

  const refresh = useCallback(async () => {
    if (!website) return;
    setError("");
    try {
      const data = await api.linkProspects(website.id, Number(minDa) || 0);
      setProspects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prospects");
      setProspects([]);
    }
  }, [website, minDa]);

  useEffect(() => {
    if (!website) {
      setInitialLoading(false);
      return;
    }
    setInitialLoading(true);
    refresh().finally(() => setInitialLoading(false));
  }, [website, refresh]);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!website) return;
    setLoading(true);
    setError("");
    setSuccess("");
    setPlan(null);
    setProspects([]);
    try {
      const res = await api.searchLinkProspects(website.id, {
        keyword,
        target_url: targetUrl,
        anchor_text: anchorText,
        min_da: Number(minDa) || 0,
        min_pa: Number(minPa) || 0,
      });
      setProspects(res.prospects);
      setPlan(res.submission_plan);
      setSuccess(`Found ${res.found} high DA/PA prospects for "${keyword}". Click the blue links below to open each site.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function markPosted(id: number) {
    if (!website) return;
    setMarkingId(id);
    setError("");
    try {
      await api.updateLinkProspect(website.id, id, {
        outreach_status: "posted",
        posted_url: postedUrlInput || undefined,
        notes: `Posted with anchor: ${anchorText}`,
      });
      setPostedUrlInput("");
      setSuccess("Marked as posted.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update prospect");
    } finally {
      setMarkingId(null);
    }
  }

  if (websiteLoading || initialLoading) {
    return <p className="text-sm text-slate-400">Loading link outreach...</p>;
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">High DA/PA Link Outreach</h2>
          <p className="text-sm text-slate-400">Search for high-authority sites, then open each link and post your URL with the target keyword</p>
        </div>
        <WebsiteSelector />
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/50 p-3 text-sm text-red-300">{error}</div>
      )}
      {success && (
        <div className="rounded-lg border border-green-800 bg-green-950/40 p-3 text-sm text-green-300">{success}</div>
      )}

      <form onSubmit={search} className="card grid gap-3 md:grid-cols-2">
        <input className="input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Target keyword" required />
        <input className="input" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} placeholder="Your URL to post" required />
        <input className="input" value={anchorText} onChange={(e) => setAnchorText(e.target.value)} placeholder="Anchor text" />
        <div className="grid grid-cols-2 gap-2">
          <input className="input" value={minDa} onChange={(e) => setMinDa(e.target.value)} placeholder="Min DA" />
          <input className="input" value={minPa} onChange={(e) => setMinPa(e.target.value)} placeholder="Min PA" />
        </div>
        <button type="submit" className="btn md:col-span-2" disabled={loading}>
          {loading ? "Searching Google (may take 10–15 seconds)..." : "Search high DA/PA prospects"}
        </button>
      </form>

      {loading && (
        <div className="card text-sm text-slate-300">
          Searching guest post, directory and citation sites… Please wait.
        </div>
      )}

      {plan && (
        <div className="card space-y-2 text-sm">
          <h3 className="font-semibold">Submission plan for your URL + keyword</h3>
          <p><span className="text-slate-400">Target URL:</span> <ProspectLink url={plan.target_url} /></p>
          <p><span className="text-slate-400">Suggested anchor:</span> {plan.suggested_anchor}</p>
          <p><span className="text-slate-400">Title:</span> {plan.title_suggestion}</p>
          <p><span className="text-slate-400">Description:</span> {plan.description_suggestion}</p>
          <p className="text-slate-400">{plan.posting_tip}</p>
        </div>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[960px] text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-3">Open link</th>
              <th className="pb-2 pr-3">DA</th>
              <th className="pb-2 pr-3">PA</th>
              <th className="pb-2 pr-3">PR</th>
              <th className="pb-2 pr-3">Site</th>
              <th className="pb-2 pr-3">Type</th>
              <th className="pb-2 pr-3">Status</th>
              <th className="pb-2 pr-3">Posted URL</th>
              <th className="pb-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {prospects.map((p) => (
              <tr key={p.id} className="border-t border-slate-800 align-top">
                <td className="py-3 pr-3">
                  <a
                    href={p.prospect_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn inline-block whitespace-nowrap"
                  >
                    Open site
                  </a>
                </td>
                <td className="py-3 pr-3 font-semibold text-brand-500">{Math.round(p.domain_authority)}</td>
                <td className="py-3 pr-3">{Math.round(p.page_authority)}</td>
                <td className="py-3 pr-3">{p.page_rank}</td>
                <td className="py-3 pr-3">
                  <p className="font-medium">{p.prospect_domain}</p>
                  <ProspectLink url={p.prospect_url} label={p.prospect_title || p.prospect_url} />
                </td>
                <td className="py-3 pr-3 capitalize">{formatStatus(p.prospect_type)}</td>
                <td className="py-3 pr-3 capitalize">{formatStatus(p.outreach_status)}</td>
                <td className="py-3 pr-3">
                  {p.posted_url ? <ProspectLink url={p.posted_url} label="View posted link" /> : <span className="text-slate-500">—</span>}
                </td>
                <td className="py-3">
                  {p.outreach_status !== "posted" && p.outreach_status !== "live" && (
                    <button
                      type="button"
                      className="btn whitespace-nowrap"
                      disabled={markingId === p.id}
                      onClick={() => markPosted(p.id)}
                    >
                      {markingId === p.id ? "Saving..." : "Mark posted"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && !prospects.length && (
          <p className="text-sm text-slate-400">No prospects yet. Click search to find high DA/PA sites for your keyword.</p>
        )}
      </div>

      <div className="card text-xs text-slate-400">
        <p className="mb-1">Optional: paste your live submission URL before marking posted</p>
        <input
          className="input"
          value={postedUrlInput}
          onChange={(e) => setPostedUrlInput(e.target.value)}
          placeholder="https://example.com/your-posted-link"
        />
      </div>
    </div>
  );
}

export default function LinkOutreachPage() {
  return <LinkOutreachContent />;
}
