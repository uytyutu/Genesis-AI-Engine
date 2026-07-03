"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TaskItem = {
  task_id: string;
  name: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  result: string;
  error: string | null;
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/tasks`);
      const data = await res.json();
      setTasks(data.tasks);
      setMessage("");
    } catch {
      setMessage("Cannot reach API — start backend on port 8000");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  async function createTask(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await fetch(`${API}/api/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
    setName("");
    refresh();
  }

  async function runNext() {
    await fetch(`${API}/api/tasks/run-next`, { method: "POST" });
    refresh();
  }

  async function cancelTask(taskId: string) {
    await fetch(`${API}/api/tasks/${taskId}/cancel`, { method: "POST" });
    refresh();
  }

  function formatDuration(ms: number | null) {
    if (ms === null) return "—";
    return `${ms.toFixed(2)} ms`;
  }

  return (
    <main className="min-h-screen pb-10">
      <header className="mb-6 rounded-xl border border-genesis-border bg-genesis-panel p-6 text-center">
        <h1 className="text-xl font-semibold">Tasks</h1>
        <p className="mt-1 text-sm text-genesis-muted">
          Live queue — UUID, status, timing, result
        </p>
      </header>

      <section className="mb-6 flex flex-wrap gap-3 rounded-xl border border-genesis-border bg-genesis-panel p-4">
        <form onSubmit={createTask} className="flex flex-1 flex-wrap gap-2">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New task name"
            className="min-w-[200px] flex-1 rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="rounded-lg bg-genesis-accent px-4 py-2 text-sm font-medium hover:opacity-90"
          >
            Create task
          </button>
        </form>
        <button
          type="button"
          onClick={runNext}
          className="rounded-lg bg-genesis-green/80 px-4 py-2 text-sm font-medium hover:bg-genesis-green"
        >
          Run next
        </button>
      </section>

      <section className="overflow-x-auto rounded-xl border border-genesis-border bg-genesis-panel">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-genesis-border text-genesis-muted">
              <th className="p-3 font-medium">ID</th>
              <th className="p-3 font-medium">Name</th>
              <th className="p-3 font-medium">Status</th>
              <th className="p-3 font-medium">Started</th>
              <th className="p-3 font-medium">Duration</th>
              <th className="p-3 font-medium">Result</th>
              <th className="p-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="p-4 text-genesis-muted">
                  Loading…
                </td>
              </tr>
            ) : tasks.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-4 text-genesis-muted">
                  No tasks yet — create one above
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr key={task.task_id} className="border-b border-genesis-border/50">
                  <td className="p-3 font-mono text-xs" title={task.task_id}>
                    {task.task_id.slice(0, 8)}…
                  </td>
                  <td className="p-3">{task.name}</td>
                  <td className="p-3 capitalize">{task.status}</td>
                  <td className="p-3 font-mono text-xs text-genesis-muted">
                    {task.started_at.slice(11, 19) || task.started_at}
                  </td>
                  <td className="p-3">{formatDuration(task.duration_ms)}</td>
                  <td className="p-3 capitalize">{task.result}</td>
                  <td className="p-3">
                    {task.status === "queued" && (
                      <button
                        type="button"
                        onClick={() => cancelTask(task.task_id)}
                        className="text-xs text-red-400 hover:underline"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      {message && <p className="mt-4 text-center text-sm text-genesis-muted">{message}</p>}
    </main>
  );
}
