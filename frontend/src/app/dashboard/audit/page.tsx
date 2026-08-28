"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    if (!website) return;
    api.issues(website.id).then(setIssues);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Technical Audit</h2>
        <WebsiteSelector />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2">Severity</th>
              <th className="pb-2">Issue</th>
              <th className="pb-2">Page</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <tr key={issue.id} className="border-t border-slate-800">
                <td className="py-2"><span className={`badge ${severityColor[issue.severity]}`}>{issue.severity}</span></td>
                <td className="py-2">{issue.message}</td>
                <td className="py-2 text-slate-400">{issue.page_url || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!issues.length && <p className="text-sm text-slate-400">No audit issues yet. Run a crawl from Overview.</p>}
      </div>
    </div>
  );
}

export default function AuditPage() {
  return <WebsiteProvider><AuditContent /></WebsiteProvider>;
}
