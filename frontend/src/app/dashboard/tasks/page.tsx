"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { OnboardingCard, useWebsite, WebsiteSelector } from "@/components/WebsiteContext";

export default function TasksPage() {
  const { website, websiteId, loading } = useWebsite();
  const [tasks, setTasks] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [tasksLoading, setTasksLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!websiteId) {
      setTasks([]);
      return;
    }
    setTasksLoading(true);
    setError("");
    try {
      setTasks(await api.tasks(websiteId));
    } catch (err) {
      setTasks([]);
      setError(err instanceof Error ? err.message : "Could not load tasks");
    } finally {
      setTasksLoading(false);
    }
  }, [websiteId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function markDone(taskId: number) {
    if (!websiteId) return;
    await api.updateTask(websiteId, taskId, { status: "completed" });
    refresh();
  }

  if (loading) return <p className="text-sm text-slate-400">Loading project...</p>;
  if (!website) return <OnboardingCard />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">SEO Task Board</h2>
        <WebsiteSelector />
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
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
                <td className="py-2 capitalize">{(t.status || "pending").replace("_", " ")}</td>
                <td className="py-2">{t.status !== "completed" && <button className="btn" onClick={() => markDone(t.id)}>Done</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {tasksLoading && <p className="p-3 text-sm text-slate-400">Loading tasks...</p>}
        {!tasksLoading && !tasks.length && (
          <p className="p-3 text-sm text-slate-400">
            No tasks yet. Use Technical SEO &gt; Create SEO tasks or AI Chat to generate prioritized actions.
          </p>
        )}
      </div>
    </div>
  );
}
