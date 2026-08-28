"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function BacklinksContent() {
  const { website } = useWebsite();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!website) return;
    api.backlinkGap(website.id).then(setData);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Backlink Gap</h2>
        <WebsiteSelector />
      </div>
      <div className="card">
        <p className="text-sm text-slate-400">{data?.note}</p>
        <p className="mt-2 text-2xl font-bold">{data?.gap_count ?? 0} gap opportunities</p>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr><th>Domain</th><th>Source URL</th><th>Anchor</th></tr>
          </thead>
          <tbody>
            {data?.gaps?.map((g: any, idx: number) => (
              <tr key={idx} className="border-t border-slate-800">
                <td className="py-2">{g.source_domain}</td>
                <td className="py-2">{g.source_url}</td>
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
  return <WebsiteProvider><BacklinksContent /></WebsiteProvider>;
}
