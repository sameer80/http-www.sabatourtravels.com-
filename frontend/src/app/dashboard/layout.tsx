"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { WebsiteProvider } from "@/components/WebsiteContext";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/websites", label: "Websites" },
  { href: "/dashboard/link-outreach", label: "Link Outreach" },
  { href: "/dashboard/keywords", label: "Keywords" },
  { href: "/dashboard/rankings", label: "Rankings" },
  { href: "/dashboard/serp", label: "Competitors" },
  { href: "/dashboard/backlinks", label: "Backlinks" },
  { href: "/dashboard/audit", label: "Technical SEO" },
  { href: "/dashboard/on-page", label: "On-Page SEO" },
  { href: "/dashboard/opportunities", label: "Content" },
  { href: "/dashboard/internal-links", label: "Internal Links" },
  { href: "/dashboard/tasks", label: "SEO Tasks" },
  { href: "/dashboard/recommendations", label: "AI Recommendations" },
  { href: "/dashboard/reports", label: "Reports" },
  { href: "/dashboard/chat", label: "AI SEO Chat" },
  { href: "/dashboard/settings", label: "Settings" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <WebsiteProvider>
      <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
        <aside className="flex max-h-screen flex-col border-b border-slate-800 bg-slate-900 p-5 lg:border-b-0 lg:border-r">
          <div className="mb-4 shrink-0">
            <p className="text-xs uppercase tracking-widest text-brand-500">Saba Tours & Travels</p>
            <h1 className="text-xl font-bold">AI SEO Manager Bot</h1>
          </div>
          <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-lg px-3 py-2 text-sm ${
                  pathname === item.href ? "bg-brand-600 text-white" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-h-screen overflow-y-auto p-6">{children}</main>
      </div>
    </WebsiteProvider>
  );
}
