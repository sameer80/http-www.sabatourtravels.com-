"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

const DEFAULT_REPORT = "https://smr.seotooladda.com/seo/31026440";

type PullResult = { message: string; synced?: number; total_backlinks?: number };

export default function BacklinksPage() {
  const { website, websiteId, loading: projectLoading } = useWebsite();
  const [data, setData] = useState<any>(null);
  const [crossPlan, setCrossPlan] = useState<any>(null);
  const [reportUrl, setReportUrl] = useState(DEFAULT_REPORT);
  const [importText, setImportText] = useState("");
  const [loading, setLoading] = useState(true);
  const [pulling, setPulling] = useState(false);
  const [pullingSemrush, setPullingSemrush] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!websiteId) return;
    setError("");
    try {
      const res = await api.backlinkGap(websiteId);
      setData(res);
      if (res.report_url) setReportUrl(res.report_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backlinks");
    }
  }, [websiteId]);

  useEffect(() => {
    api.crossLinkPlan().then(setCrossPlan).catch(() => {});
  }, []);

  useEffect(() => {
    if (!websiteId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [websiteId, refresh]);

  async function pullNew(replace = false) {
    if (!websiteId) return;
    setPulling(true);
    setError("");
    setMessage("");
    try {
      let importRows;
      if (importText.trim()) {
        const parsed = JSON.parse(importText);
        importRows = Array.isArray(parsed) ? parsed : parsed.backlinks;
      }
      const res = (await api.pullBacklinks(websiteId, {
        report_url: reportUrl,
        replace_existing: replace,
        import_rows: importRows,
      })) as PullResult;
      setMessage(res.message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pull failed");
    } finally {
      setPulling(false);
    }
  }

  async function pullSemrush() {
    if (!websiteId) return;
    setPullingSemrush(true);
    setError("");
    setMessage("");
    try {
      const res = await api.pullSemrushBacklinks(websiteId);
      setMessage(res.message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "SEMrush pull failed. Set SEMRUSH_API_KEY in backend .env");
    } finally {
      setPullingSemrush(false);
    }
  }

  if (projectLoading) return <p className="text-sm text-slate-400">Loading project...</p>;
  if (!website) return <OnboardingCard />;
  if (loading) return <p className="text-sm text-slate-400">Loading backlinks...</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Backlinks</h2>
          <p className="text-sm text-slate-400">SEMrush pull, SEO Tool Adda, and cross-site links for {website.domain}</p>
        </div>
        <WebsiteSelector />
      </div>

      <div className="card space-y-3">
        <h3 className="font-semibold">SEMrush API pull</h3>
        <p className="text-sm text-slate-400">
          Set <code className="text-brand-400">SEMRUSH_API_KEY</code> in backend <code className="text-brand-400">.env</code> and restart the backend.
          Requires SEMrush Backlinks API units on your account.
        </p>
        <div className="flex flex-wrap gap-2">
          <button className="btn" onClick={pullSemrush} disabled={pullingSemrush || pulling}>
            {pullingSemrush ? "Pulling from SEMrush..." : "Pull from SEMrush"}
          </button>
          <span className="self-center text-xs text-slate-500">Or run: python scripts/semrush-pull-backlinks.py</span>
        </div>
      </div>

      <div className="card space-y-3">
        <h3 className="font-semibold">SEO Tool Adda report</h3>
        <label className="text-sm text-slate-400">Report URL</label>
        <input className="input" value={reportUrl} onChange={(e) => setReportUrl(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <a href={reportUrl} target="_blank" rel="noreferrer" className="btn bg-slate-700 hover:bg-slate-600">
            Open SEO Tool Adda
          </a>
          <button className="btn" onClick={() => pullNew(false)} disabled={pulling || pullingSemrush}>
            {pulling ? "Pulling..." : "Pull new report"}
          </button>
          <button className="btn bg-slate-700 hover:bg-slate-600" onClick={() => pullNew(true)} disabled={pulling || pullingSemrush}>
            Replace all and pull
          </button>
        </div>
        <textarea
          className="input min-h-[80px]"
          placeholder='Optional import JSON: [{"source_url":"...","target_url":"https://sabacabs.com/","anchor_text":"..."}]'
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
        />
      </div>

      <div className="card space-y-3">
        <h3 className="font-semibold">Auto-post cross-links (your 3 websites only)</h3>
        <p className="text-sm text-slate-400">
          Posts partner links between onewaydrop.cab, sabacabs.com and punetomumbaicabservice.com using Selenium WebDriver on your PC.
          Only for sites you own. Start with <code className="text-brand-400">dry_run: true</code>.
        </p>
        {crossPlan?.plan?.length ? (
          <ul className="space-y-1 text-sm text-slate-300">
            {crossPlan.plan.slice(0, 6).map((item: any) => (
              <li key={`${item.source_domain}-${item.target_domain}`}>
                <strong>{item.source_domain}</strong> -&gt; {item.target_url} ({item.anchor_text})
              </li>
            ))}
            {crossPlan.plan.length > 6 && (
              <li className="text-slate-500">+ {crossPlan.plan.length - 6} more cross-links in plan</li>
            )}
          </ul>
        ) : null}
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-400">
          <li>Copy <code>scripts/link-post-config.example.json</code> to <code>scripts/link-post-config.json</code></li>
          <li>Set WordPress env vars: <code>WP_SABACABS_USER</code>, <code>WP_SABACABS_PASS</code>, etc.</li>
          <li><code>pip install -r scripts/requirements-selenium.txt</code></li>
          <li><code>python scripts/post-portfolio-links-selenium.py</code> (Windows: run from repo folder)</li>
        </ol>
      </div>

      {error && <div className="rounded-lg border border-red-800 bg-red-950/50 p-3 text-sm text-red-300">{error}</div>}
      {message && <div className="rounded-lg border border-green-800 bg-green-950/40 p-3 text-sm text-green-300">{message}</div>}

      <div className="grid gap-3 md:grid-cols-4">
        {[
          ["Total backlinks", data?.total_backlinks ?? 0],
          ["Referring domains", data?.referring_domains ?? 0],
          ["New links", data?.new_backlinks ?? 0],
          ["Gap opportunities", data?.gap_count ?? 0],
        ].map(([label, value]) => (
          <div key={label as string} className="card">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="card overflow-x-auto">
        <h3 className="mb-3 font-semibold">Your backlinks</h3>
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-3">Domain</th>
              <th className="pb-2 pr-3">Source URL</th>
              <th className="pb-2 pr-3">Target</th>
              <th className="pb-2 pr-3">Anchor</th>
              <th className="pb-2">New</th>
            </tr>
          </thead>
          <tbody>
            {data?.backlinks?.map((b: any) => (
              <tr key={b.id} className="border-t border-slate-800">
                <td className="py-2 pr-3">{b.source_domain}</td>
                <td className="py-2 pr-3">
                  <a href={b.source_url} target="_blank" rel="noreferrer" className="table-link break-all">
                    {b.source_url}
                  </a>
                </td>
                <td className="py-2 pr-3 break-all">{b.target_url}</td>
                <td className="py-2 pr-3">{b.anchor_text || "-"}</td>
                <td className="py-2">{b.is_new ? "Yes" : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data?.backlinks?.length && (
          <p className="text-sm text-slate-400">No backlinks yet. Click Pull from SEMrush or Pull new report.</p>
        )}
      </div>

      <div className="card overflow-x-auto">
        <h3 className="mb-3 font-semibold">Competitor gap opportunities</h3>
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr><th>Domain</th><th>Source URL</th><th>Anchor</th></tr>
          </thead>
          <tbody>
            {data?.gaps?.map((g: any, idx: number) => (
              <tr key={idx} className="border-t border-slate-800">
                <td className="py-2">{g.source_domain}</td>
                <td className="py-2"><a href={g.source_url} target="_blank" rel="noreferrer" className="table-link">{g.source_url}</a></td>
                <td className="py-2">{g.anchor_text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
