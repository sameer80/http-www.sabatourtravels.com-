"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { fixGuide } from "@/lib/seoFixes";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

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
  const [creatingTasks, setCreatingTasks] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const loadIssues = useCallback(async () => {
    if (!website) return;
    setError("");
    try {
      setIssues(await api.issues(website.id));
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
    setCrawlMeta({ pages: latest.pages_crawled, issues: latest.issues_found, error: latest.error_message });
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
    setSuccess("");
    setCrawlStatus("running");
    try {
      await api.startCrawl(website.id);
      setCrawlMeta({ pages: 0, issues: 0 });
    } catch (err) {
      setCrawling(false);
      setError(err instanceof Error ? err.message : "Could not start crawl");
    }
  }

  async function createTasks() {
    if (!website) return;
    setCreatingTasks(true);
    setError("");
    setSuccess("");
    try {
      const tasks = await api.createTasksFromAudit(website.id);
      setSuccess(`Created ${tasks.length} SEO tasks. Open SEO Tasks to fix each page in WordPress/Hostinger.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create tasks");
    } finally {
      setCreatingTasks(false);
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
          <p className="text-sm text-slate-400">Scanning live pages on {website.domain}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <WebsiteSelector />
          <button className="btn" onClick={runAuditCrawl} disabled={crawling}>
            {crawling ? "Crawling..." : "Run audit crawl"}
          </button>
          <button className="btn bg-slate-700 hover:bg-slate-600" onClick={createTasks} disabled={creatingTasks || !issues.length}>
            {creatingTasks ? "Creating..." : "Create SEO tasks"}
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-brand-700/40 bg-brand-950/20 p-4 text-sm text-slate-200">
        <p className="font-medium text-brand-100">How local SEO fixing works</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-300">
          <li><strong>localhost:3000</strong> = SEO dashboard on your PC (analysis only)</li>
          <li><strong>{website.domain}</strong> = live website you edit in WordPress / Hostinger</li>
          <li>Use <Link href="/dashboard/on-page" className="table-link">On-Page SEO</Link> for per-page fix steps, then edit the live page and re-crawl to verify</li>
        </ul>
      </div>

      {error && <div className="rounded-lg border border-red-800 bg-red-950/50 p-3 text-sm text-red-300">{error}</div>}
      {success && <div className="rounded-lg border border-green-800 bg-green-950/40 p-3 text-sm text-green-300">{success}</div>}

      {crawlStatus && (
        <div className="card text-sm text-slate-300">
          <p>
            <span className="text-slate-400">Last crawl:</span> <span className="capitalize">{crawlStatus}</span>
            {crawlMeta?.pages != null ? ` · ${crawlMeta.pages} pages · ${crawlMeta.issues ?? 0} issues` : ""}
          </p>
          {crawling && <p className="mt-1 text-brand-100">Crawling can take 1–3 minutes. Page refreshes automatically.</p>}
        </div>
      )}

      {rateLimited && (
        <div className="rounded-lg border border-yellow-700 bg-yellow-950/30 p-3 text-sm text-yellow-200">
          Rate limited (HTTP 429). Wait 1–2 minutes, then click <strong>Run audit crawl</strong> again.
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
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-3">Severity</th>
              <th className="pb-2 pr-3">Issue</th>
              <th className="pb-2 pr-3">How to fix (WordPress)</th>
              <th className="pb-2 pr-3">Live page</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <tr key={issue.id} className="border-t border-slate-800 align-top">
                <td className="py-3 pr-3">
                  <span className={`badge ${severityColor[issue.severity] || "bg-slate-600"}`}>{issue.severity}</span>
                </td>
                <td className="py-3 pr-3">{issue.message}</td>
                <td className="py-3 pr-3 text-slate-300">{fixGuide(issue.issue_type)}</td>
                <td className="py-3 pr-3">
                  {issue.page_url ? (
                    <a href={issue.page_url} target="_blank" rel="noreferrer" className="btn inline-block whitespace-nowrap">
                      Open live page
                    </a>
                  ) : (
                    <span className="text-slate-500">Site-wide</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!issues.length && (
          <p className="text-sm text-slate-400">
            No issues yet. Select <strong>Saba Cabs (sabacabs.com)</strong> and click <strong>Run audit crawl</strong>.
          </p>
        )}
      </div>
    </div>
  );
}

export default function AuditPage() {
  return <AuditContent />;
}
