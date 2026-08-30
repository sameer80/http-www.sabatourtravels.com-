"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

const DEFAULT_REPORT = "https://smr.seotooladda.com/seo/31026440";

function BacklinksContent() {
  const { website } = useWebsite();
  const [data, setData] = useState<any>(null);
  const [reportUrl, setReportUrl] = useState(DEFAULT_REPORT);
  const [importText, setImportText] = useState("");
  const [loading, setLoading] = useState(true);
  const [pulling, setPulling] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!website) return;
    setError("");
    try {
      const res = await api.backlinkGap(website.id);
      setData(res);
      if (res.report_url) setReportUrl(res.report_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backlinks");
    }
  }, [website]);

  useEffect(() => {
    if (!website) {
      setLoading(false);
      return;
    }
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [website, refresh]);

  async function pullNew(replace = false) {
    if (!website) return;
    setPulling(true);
    setError("");
    setMessage("");
    try {
      let importRows;
      if (importText.trim()) {
        const parsed = JSON.parse(importText);
        importRows = Array.isArray(parsed) ? parsed : parsed.backlinks;
      }
      const res = await api.pullBacklinks(website.id, {
        report_url: reportUrl,
        replace_existing: replace,
        import_rows: importRows,
      });
      setMessage(res.message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pull failed");
    } finally {
      setPulling(false);
    }
  }

  if (!website) return <OnboardingCard />;
  if (loading) return <p className="text-sm text-slate-400">Loading backlinks...</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Backlinks</h2>
          <p className="text-sm text-slate-400">Linked to SEO Tool Adda report for {website.domain}</p>
        </div>
        <WebsiteSelector />
      </div>

      <div className="card space-y-3">
        <label className="text-sm text-slate-400">SEO Tool Adda report URL</label>
        <input className="input" value={reportUrl} onChange={(e) => setReportUrl(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <a href={reportUrl} target="_blank" rel="noreferrer" className="btn bg-slate-700 hover:bg-slate-600">
            Open SEO Tool Adda
          </a>
          <button className="btn" onClick={() => pullNew(false)} disabled={pulling}>
            {pulling ? "Pulling..." : "Pull new report"}
          </button>
          <button className="btn bg-slate-700 hover:bg-slate-600" onClick={() => pullNew(true)} disabled={pulling}>
            Replace all & pull
          </button>
        </div>
        <p className="text-xs text-slate-400">
          Pull saves the report link and discovers new referring domains. For exact Ahrefs/Semrush rows, export from SEO Tool Adda and paste JSON below, then click Pull.
        </p>
        <textarea
          className="input min-h-[80px]"
          placeholder='Optional import JSON: [{"source_url":"...","target_url":"https://sabacabs.com/","anchor_text":"..."}]'
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
        />
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
                <td className="py-2 pr-3">{b.anchor_text || "—"}</td>
                <td className="py-2">{b.is_new ? "Yes" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data?.backlinks?.length && (
          <p className="text-sm text-slate-400">No backlinks yet. Click <strong>Pull new report</strong>.</p>
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

export default function BacklinksPage() {
  return (
    <WebsiteProvider>
      <BacklinksContent />
    </WebsiteProvider>
  );
}
