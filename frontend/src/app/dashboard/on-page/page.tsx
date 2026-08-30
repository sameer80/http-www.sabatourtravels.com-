"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { fixGuide } from "@/lib/seoFixes";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function OnPageContent() {
  const { website } = useWebsite();
  const [pagesByIssue, setPagesByIssue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!website) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api.auditByPage(website.id).then(setPagesByIssue).finally(() => setLoading(false));
  }, [website]);

  if (!website) return <OnboardingCard />;
  if (loading) return <p className="text-sm text-slate-400">Loading on-page SEO...</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">On-Page SEO — Fix Each Page</h2>
          <p className="text-slate-400">
            Edit these URLs in WordPress/Hostinger, then re-run audit crawl on Technical SEO
          </p>
        </div>
        <WebsiteSelector />
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 text-sm text-slate-300">
        This dashboard runs on your PC, but each page below is the <strong>live {website.domain} URL</strong>.
        Open the page → fix in WordPress → click <strong>Run audit crawl</strong> on Technical SEO to confirm.
      </div>

      <div className="space-y-4">
        {pagesByIssue.map((group) => (
          <div key={group.page_url || group.page_path} className="card space-y-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{group.page_title || group.page_path}</p>
                <p className="text-xs text-slate-400">{group.page_path}</p>
              </div>
              {group.page_url && (
                <a href={group.page_url} target="_blank" rel="noreferrer" className="btn whitespace-nowrap">
                  Open live page
                </a>
              )}
            </div>
            <div className="space-y-2">
              {group.issues.map((issue: any) => (
                <div key={issue.id} className="rounded-lg bg-slate-800/80 p-3 text-sm">
                  <p><span className="badge bg-slate-600 mr-2">{issue.severity}</span>{issue.message}</p>
                  <p className="mt-2 text-slate-300"><strong>Fix:</strong> {fixGuide(issue.issue_type)}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
        {!pagesByIssue.length && (
          <p className="text-sm text-slate-400">
            No page data yet. Go to Technical SEO → Run audit crawl for {website.domain}.
          </p>
        )}
      </div>
    </div>
  );
}

export default function OnPagePage() {
  return (
    <WebsiteProvider>
      <OnPageContent />
    </WebsiteProvider>
  );
}
