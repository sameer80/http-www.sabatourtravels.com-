"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function RecommendationsContent() {
  const { website } = useWebsite();
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    if (!website) return;
    api.recommendations(website.id).then(setItems);
  }, [website]);

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">AI Recommendations</h2>
          <p className="text-slate-400">Evidence-based actions with priority, owner and validation method (SRS §15)</p>
        </div>
        <WebsiteSelector />
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="card space-y-2">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="font-semibold">{item.title}</h3>
              <div className="flex gap-2">
                <span className="badge bg-brand-700">{item.score}</span>
                <span className="badge bg-slate-700">{item.priority}</span>
              </div>
            </div>
            <p className="text-sm text-slate-300">{item.evidence}</p>
            <div className="grid gap-2 text-xs text-slate-400 md:grid-cols-3">
              <p><strong>Owner:</strong> {item.suggested_owner}</p>
              <p><strong>Type:</strong> {item.opportunity_type}</p>
              <p><strong>Validation:</strong> {item.validation_method}</p>
            </div>
          </div>
        ))}
        {!items.length && <p className="text-sm text-slate-400">No recommendations yet. Add keywords and run opportunity refresh.</p>}
      </div>
    </div>
  );
}

export default function RecommendationsPage() {
  return (
    <WebsiteProvider>
      <RecommendationsContent />
    </WebsiteProvider>
  );
}
