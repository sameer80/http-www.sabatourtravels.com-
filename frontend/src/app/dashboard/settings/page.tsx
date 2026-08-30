"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function SettingsContent() {
  const { website } = useWebsite();
  const [syncResult, setSyncResult] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);

  async function runSemrushSync() {
    if (!website) return;
    setSyncing(true);
    try {
      setSyncResult(await api.syncSemrush(website.id));
    } catch (err) {
      setSyncResult({ status: "failed", message: err instanceof Error ? err.message : "Sync failed" });
    } finally {
      setSyncing(false);
    }
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-slate-400">Integrations and security (SRS §6, §23)</p>
        </div>
        <WebsiteSelector />
      </div>

      <div className="card space-y-3">
        <h3 className="font-semibold">SEMrush API</h3>
        <p className="text-sm text-slate-400">
          Set <code className="text-brand-400">SEMRUSH_API_KEY</code> in your backend environment. Credentials are never stored in source code.
        </p>
        <button className="btn" onClick={runSemrushSync} disabled={syncing}>
          {syncing ? "Syncing..." : "Sync rankings from SEMrush"}
        </button>
        {syncResult && (
          <p className="text-sm text-slate-300">
            Status: {syncResult.status}
            {syncResult.message ? ` — ${syncResult.message}` : ""}
            {syncResult.records_synced ? ` (${syncResult.records_synced} records)` : ""}
          </p>
        )}
      </div>

      <div className="card space-y-2 text-sm text-slate-400">
        <h3 className="font-semibold text-slate-200">Other integrations</h3>
        <p><strong>OPENAI_API_KEY</strong> — GPT-powered AI SEO chat</p>
        <p><strong>OPENPAGERANK_API_KEY</strong> — Link prospect authority scores</p>
        <p><strong>Google Search Console</strong> — Phase 2 (import via GSC metrics API)</p>
        <p className="text-xs">Human approval required before publishing content or production SEO changes (SRS §24).</p>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <WebsiteProvider>
      <SettingsContent />
    </WebsiteProvider>
  );
}
