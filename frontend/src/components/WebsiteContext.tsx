"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Website = { id: number; name: string; domain: string; base_url: string };

const WebsiteContext = createContext<{
  website: Website | null;
  websites: Website[];
  loading: boolean;
  setWebsiteId: (id: number) => void;
  refreshWebsites: () => Promise<void>;
}>({ website: null, websites: [], loading: true, setWebsiteId: () => {}, refreshWebsites: async () => {} });

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

  function setWebsiteId(id: number) {
    setWebsiteIdState(id);
    sessionStorage.setItem("websiteId", String(id));
  }

  async function refreshWebsites() {
    const data = await api.websites();
    setWebsites(data);
    setWebsiteIdState((current) => {
      const next = current && data.some((w) => w.id === current) ? current : data[0]?.id ?? null;
      if (next) sessionStorage.setItem("websiteId", String(next));
      return next;
    });
  }

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/");
      return;
    }
    setLoading(true);
    refreshWebsites()
      .catch(() => router.push("/"))
      .finally(() => setLoading(false));
  }, [router]);

  const website = websites.find((w) => w.id === websiteId) || null;

  return (
    <WebsiteContext.Provider value={{ website, websites, loading, setWebsiteId, refreshWebsites }}>
      {children}
    </WebsiteContext.Provider>
  );
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
        <option key={w.id} value={w.id}>{w.name} ({w.domain})</option>
      ))}
    </select>
  );
}

export function OnboardingCard() {
  const { refreshWebsites } = useWebsite();
  const [name, setName] = useState("Saba Cabs");
  const [domain, setDomain] = useState("sabacabs.com");
  const [baseUrl, setBaseUrl] = useState("https://sabacabs.com");
  const [loading, setLoading] = useState(false);

  async function createWebsite(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await api.createWebsite({ name, domain, base_url: baseUrl, country: "IN", city: "Pune", language: "en" });
    await refreshWebsites();
    setLoading(false);
  }

  return (
    <form onSubmit={createWebsite} className="card mx-auto max-w-xl space-y-3">
      <h2 className="text-lg font-semibold">Add your first website</h2>
      <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" />
      <input className="input" value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain" />
      <input className="input" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="Base URL" />
      <button className="btn" disabled={loading}>{loading ? "Saving..." : "Add website"}</button>
    </form>
  );
}
