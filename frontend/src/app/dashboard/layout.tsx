"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/audit", label: "Technical Audit" },
  { href: "/dashboard/keywords", label: "Keywords" },
  { href: "/dashboard/opportunities", label: "Opportunities" },
  { href: "/dashboard/tasks", label: "Task Board" },
  { href: "/dashboard/serp", label: "SERP Analysis" },
  { href: "/dashboard/internal-links", label: "Internal Links" },
  { href: "/dashboard/backlinks", label: "Backlink Gap" },
  { href: "/dashboard/link-outreach", label: "Link Outreach" },
  { href: "/dashboard/chat", label: "AI SEO Chat" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-slate-800 bg-slate-900 p-5 lg:border-b-0 lg:border-r">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-widest text-brand-500">AI SEO Manager</p>
          <h1 className="text-xl font-bold">SEO Command Center</h1>
        </div>
        <nav className="space-y-1">
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
      <main className="p-6">{children}</main>
    </div>
  );
}
