"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

const severityColor: Record<string, string> = {
  critical: "bg-red-600",
  high: "bg-orange-600",
  medium: "bg-yellow-600",
  low: "bg-slate-600",
};

function AuditContent() {
  const { website } = useWebsite();
  const [issues, setIssues] = useState<any[]>([]);
  const [crawlStatus, setCrawlStatus] = useState<string | null>(null);
  const [crawlMeta, setCrawlMeta] = useState<{ pages?: number; issues?: number; error?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);
  const [error, setError] = useState("");

  const loadIssues = useCallback(async () => {
    if (!website) return;
    setError("");
    try {
      const data = await api.issues(website.id);
      setIssues(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit issues");
      setIssues([]);
    }
  }, [website]);

  const loadCrawlStatus = useCallback(async () => {
    if (!website) return null;
    const runs = await api.crawlRuns(website.id);
    const latest = runs[0];
    if (!latest) return null;
    setCrawlStatus(latest.status);
    setCrawlMeta({
      pages: latest.pages_crawled,
      issues: latest.issues_found,
      error: latest.error_message,
    });
    return latest.status as string;
  }, [website]);

  useEffect(() => {
    if (!website) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([loadIssues(), loadCrawlStatus()]).finally(() => setLoading(false));
  }, [website, loadIssues, loadCrawlStatus]);

  useEffect(() => {
    if (!website || !crawling) return;
    const timer = setInterval(async () => {
      const status = await loadCrawlStatus();
      if (status === "completed" || status === "failed") {
        await loadIssues();
        setCrawling(false);
      }
    }, 5000);
    return () => clearInterval(timer);
  }, [website, crawling, loadCrawlStatus, loadIssues]);

  async function runAuditCrawl() {
    if (!website) return;
    setCrawling(true);
    setError("");
    setCrawlStatus("running");
    try {
      await api.startCrawl(website.id);
      setCrawlMeta({ pages: 0, issues: 0 });
    } catch (err) {
      setCrawling(false);
      setError(err instanceof Error ? err.message : "Could not start crawl");
    }
  }

  const severityCounts = useMemo(() => {
    return issues.reduce<Record<string, number>>((acc, issue) => {
      acc[issue.severity] = (acc[issue.severity] || 0) + 1;
      return acc;
    }, {});
  }, [issues]);

  const rateLimited = issues.some((issue) => issue.issue_type === "rate_limited");

  if (!website) return <OnboardingCard />;
  if (loading) return <p className="text-sm text-slate-400">Loading technical audit...</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Technical SEO Audit</h2>
          <p className="text-sm text-slate-400">
            Audits {website.domain} over HTTPS — no FTP login required
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <WebsiteSelector />
          <button className="btn" onClick={runAuditCrawl} disabled={crawling}>
            {crawling ? "Crawling site..." : "Run audit crawl"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/50 p-3 text-sm text-red-300">{error}</div>
      )}

      {crawlStatus && (
        <div className="card text-sm text-slate-300">
          <p>
            <span className="text-slate-400">Last crawl:</span>{" "}
            <span className="capitalize">{crawlStatus}</span>
            {crawlMeta?.pages != null ? ` · ${crawlMeta.pages} pages · ${crawlMeta.issues ?? 0} issues` : ""}
          </p>
          {crawlMeta?.error && <p className="mt-1 text-red-300">{crawlMeta.error}</p>}
          {crawling && <p className="mt-1 text-brand-100">Crawling can take 1–3 minutes for sabacabs.com. This page refreshes automatically.</p>}
        </div>
      )}

      {rateLimited && (
        <div className="rounded-lg border border-yellow-700 bg-yellow-950/30 p-3 text-sm text-yellow-200">
          sabacabs.com (Hostinger CDN) is rate-limiting automated crawlers (HTTP 429). Wait 1–2 minutes, then click
          <strong> Run audit crawl </strong> again. Your FTP/hosting login is not used by this SEO tool.
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-4">
        {["critical", "high", "medium", "low"].map((severity) => (
          <div key={severity} className="card">
            <p className="text-sm capitalize text-slate-400">{severity}</p>
            <p className="text-2xl font-bold">{severityCounts[severity] || 0}</p>
          </div>
        ))}
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-3">Severity</th>
              <th className="pb-2 pr-3">Issue</th>
              <th className="pb-2 pr-3">Type</th>
              <th className="pb-2">Page</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <tr key={issue.id} className="border-t border-slate-800 align-top">
                <td className="py-3 pr-3">
                  <span className={`badge ${severityColor[issue.severity] || "bg-slate-600"}`}>{issue.severity}</span>
                </td>
                <td className="py-3 pr-3">{issue.message}</td>
                <td className="py-3 pr-3 text-slate-400">{issue.issue_type}</td>
                <td className="py-3">
                  {issue.page_url ? (
                    <a href={issue.page_url} target="_blank" rel="noreferrer" className="table-link break-all">
                      {issue.page_url}
                    </a>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!issues.length && (
          <p className="text-sm text-slate-400">
            No audit issues yet. Click <strong>Run audit crawl</strong> to scan {website.domain}.
          </p>
        )}
      </div>
    </div>
  );
}

export default function AuditPage() {
  return (
    <WebsiteProvider>
      <AuditContent />
    </WebsiteProvider>
  );
}
