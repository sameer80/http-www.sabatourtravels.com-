"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Website = { id: number; name: string; domain: string; base_url: string };

const WebsiteContext = createContext<{
  website: Website | null;
  websiteId: number | null;
  websites: Website[];
  loading: boolean;
  setWebsiteId: (id: number) => void;
  refreshWebsites: () => Promise<void>;
}>({
  website: null,
  websiteId: null,
  websites: [],
  loading: true,
  setWebsiteId: () => {},
  refreshWebsites: async () => {},
});

export function useWebsite() {
  return useContext(WebsiteContext);
}

export function WebsiteProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [websites, setWebsites] = useState<Website[]>([]);
  const [websiteId, setWebsiteIdState] = useState<number | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = sessionStorage.getItem("websiteId");
    return stored ? Number(stored) : null;
  });
  const [loading, setLoading] = useState(true);

  const setWebsiteId = useCallback((id: number) => {
    setWebsiteIdState(id);
    sessionStorage.setItem("websiteId", String(id));
  }, []);

  const refreshWebsites = useCallback(async () => {
    const data = await api.websites();
    setWebsites(data);
    setWebsiteIdState((current) => {
      const next = current && data.some((w) => w.id === current) ? current : data[0]?.id ?? null;
      if (next === current) return current;
      if (next) sessionStorage.setItem("websiteId", String(next));
      else sessionStorage.removeItem("websiteId");
      return next;
    });
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/");
      return;
    }
    setLoading(true);
    refreshWebsites()
      .catch(() => {
        // Keep the user on the dashboard if the API is temporarily unreachable.
      })
      .finally(() => setLoading(false));
  }, [router, refreshWebsites]);

  const website = useMemo(
    () => websites.find((w) => w.id === websiteId) || null,
    [websites, websiteId]
  );

  const value = useMemo(
    () => ({ website, websiteId, websites, loading, setWebsiteId, refreshWebsites }),
    [website, websiteId, websites, loading, setWebsiteId, refreshWebsites]
  );

  return <WebsiteContext.Provider value={value}>{children}</WebsiteContext.Provider>;
}

export function WebsiteGate({ children }: { children: React.ReactNode }) {
  const { website, loading } = useWebsite();
  if (loading) return <p className="text-sm text-slate-400">Loading project...</p>;
  if (!website) return <OnboardingCard />;
  return <>{children}</>;
}

export function WebsiteSelector() {
  const { website, websites, setWebsiteId } = useWebsite();
  return (
    <select
      className="input max-w-xs"
      value={website?.id || ""}
      onChange={(e) => setWebsiteId(Number(e.target.value))}
    >
      {websites.map((w) => (
        <option key={w.id} value={w.id}>
          {w.name} ({w.domain})
        </option>
      ))}
    </select>
  );
}

export function OnboardingCard() {
  const { refreshWebsites } = useWebsite();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function setupPortfolio(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.bootstrapSabaTours();
      await refreshWebsites();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={setupPortfolio} className="card mx-auto max-w-xl space-y-4">
      <h2 className="text-lg font-semibold">Setup Saba Tours SEO Portfolio</h2>
      <p className="text-sm text-slate-400">
        Configure all three websites from the SRS: onewaydrop.cab, sabacabs.com and punetomumbaicabservice.com
        with priority keywords and demo ranking data.
      </p>
      <ul className="space-y-2 text-sm text-slate-300">
        <li><strong>onewaydrop.cab</strong> - One-way cab specialist</li>
        <li><strong>sabacabs.com</strong> - Cab + airport + outstation</li>
        <li><strong>punetomumbaicabservice.com</strong> - Pune-Mumbai specialist</li>
      </ul>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button className="btn w-full" disabled={loading}>
        {loading ? "Setting up..." : "Setup all 3 websites"}
      </button>
    </form>
  );
}
