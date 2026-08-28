"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

function TasksContent() {
  const { website } = useWebsite();
  const [tasks, setTasks] = useState<any[]>([]);

  async function refresh() {
    if (!website) return;
    setTasks(await api.tasks(website.id));
  }

  useEffect(() => { refresh(); }, [website]);

  async function markDone(taskId: number) {
    if (!website) return;
    await api.updateTask(website.id, taskId, { status: "completed" });
    refresh();
  }

  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">SEO Task Board</h2>
        <WebsiteSelector />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr><th>Priority</th><th>Task</th><th>Page</th><th>Reason</th><th>Owner</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} className="border-t border-slate-800">
                <td className="py-2 capitalize">{t.priority}</td>
                <td className="py-2">{t.title}</td>
                <td className="py-2">{t.page_path || "-"}</td>
                <td className="py-2 text-slate-400">{t.reason}</td>
                <td className="py-2">{t.owner}</td>
                <td className="py-2 capitalize">{t.status.replace("_", " ")}</td>
                <td className="py-2">{t.status !== "completed" && <button className="btn" onClick={() => markDone(t.id)}>Done</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!tasks.length && <p className="text-sm text-slate-400">No tasks yet. Use AI Chat to generate prioritized actions.</p>}
      </div>
    </div>
  );
}

export default function TasksPage() {
  return <WebsiteProvider><TasksContent /></WebsiteProvider>;
}
