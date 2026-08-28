"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function InternalLinksContent() {
  const { website } = useWebsite();
  const [links, setLinks] = useState<any[]>([]);

  useEffect(() => {
    if (!website) return;
    api.internalLinks(website.id).then(setLinks);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Internal Links</h2>
        <WebsiteSelector />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr><th>Source</th><th>Target</th><th>Anchor</th><th>Reason</th></tr>
          </thead>
          <tbody>
            {links.map((l, idx) => (
              <tr key={idx} className="border-t border-slate-800">
                <td className="py-2">{l.source_page}</td>
                <td className="py-2">{l.target_page}</td>
                <td className="py-2">{l.anchor_text}</td>
                <td className="py-2 text-slate-400">{l.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!links.length && <p className="text-sm text-slate-400">Run a crawl to map internal links and orphan pages.</p>}
      </div>
    </div>
  );
}

export default function InternalLinksPage() {
  return <WebsiteProvider><InternalLinksContent /></WebsiteProvider>;
}
