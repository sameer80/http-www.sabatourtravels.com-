"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function OnPageContent() {
  const { website } = useWebsite();
  const [pages, setPages] = useState<any[]>([]);

  useEffect(() => {
    if (!website) return;
    api.pages(website.id).then(setPages);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">On-Page SEO</h2>
          <p className="text-slate-400">Titles, meta, headings, content depth and internal links per page</p>
        </div>
        <WebsiteSelector />
      </div>
      <div className="space-y-3">
        {pages.map((page) => (
          <div key={page.id} className="card text-sm">
            <p className="font-medium">{page.path}</p>
            <p className="text-slate-400">{page.title || "Missing title"}</p>
            <div className="mt-2 grid gap-1 text-xs text-slate-400 md:grid-cols-4">
              <span>H1: {page.h1 || "Missing"}</span>
              <span>Words: {page.word_count}</span>
              <span>In links: {page.internal_links_in}</span>
              <span>Missing ALT: {page.images_missing_alt}</span>
            </div>
          </div>
        ))}
        {!pages.length && <p className="text-sm text-slate-400">Run a crawl to analyze on-page SEO signals.</p>}
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
