"use client";

import { useCallback, useEffect, useState } from "react";

import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SystemStatus = {
  name: string;
  version: string;
  phase: string;
  paused: boolean;
};

type Module = { id: string; label: string; status: string };

type QueueStats = {
  pending: number;
  running: number;
  completed: number;
  failed: number;
};

type ActivityEvent = {
  at: string;
  message: string;
  task_id?: string | null;
};

function statusDot(status: string, moduleId: string) {
  if (status === "online") return "bg-genesis-green";
  if (status === "degraded") return "bg-yellow-500";
  const core = ["kernel", "brain", "queue", "audit"];
  if (status === "offline" && core.includes(moduleId)) return "bg-red-500";
  return "bg-gray-600";
}

export default function MonitorPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [queue, setQueue] = useState<QueueStats | null>(null);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [s, m, q, a] = await Promise.all([
        fetch(`${API}/api/status`).then((r) => r.json()),
        fetch(`${API}/api/modules`).then((r) => r.json()),
        fetch(`${API}/api/queue`).then((r) => r.json()),
        fetch(`${API}/api/activity`).then((r) => r.json()),
      ]);
      setStatus(s);
      setModules(m.modules);
      setQueue(q);
      setActivity(a.events);
      setMessage("");
    } catch {
      setMessage(`API недоступен — запустите ${BRAND_NAME} через Launcher`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  async function runDemo() {
    setMessage("Демо…");
    const res = await fetch(`${API}/api/demo/run`, { method: "POST" });
    const data = await res.json();
    setMessage(data.message);
    refresh();
  }

  async function control(action: "pause" | "resume" | "stop") {
    const res = await fetch(`${API}/api/control/${action}`, { method: "POST" });
    const data = await res.json();
    setMessage(data.message);
    refresh();
  }

  return (
    <main className="min-h-screen pb-10 md:px-4">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="rounded-xl border border-genesis-border bg-genesis-panel p-6 text-center">
          <h1 className="text-2xl font-semibold tracking-wide">Панель управления</h1>
          <p className="mt-1 text-sm text-genesis-muted">Мониторинг системы</p>
          {status && (
            <p className="mt-2 text-xs text-genesis-muted">
              v{status.version} · {status.phase}
              {status.paused && (
                <span className="ml-2 rounded bg-yellow-600/30 px-2 py-0.5 text-yellow-300">
                  ПАУЗА
                </span>
              )}
            </p>
          )}
        </header>

        <section className="rounded-xl border border-genesis-border bg-genesis-panel p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-genesis-muted">
            Состояние модулей
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {modules.map((mod) => (
              <div
                key={mod.id}
                className="flex items-center gap-2 rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2"
              >
                <span className={`h-2.5 w-2.5 rounded-full ${statusDot(mod.status, mod.id)}`} />
                <span className="text-sm">{mod.label}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-genesis-border bg-genesis-panel p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-genesis-muted">
            Очередь задач
          </h2>
          {loading ? (
            <p className="text-sm text-genesis-muted">Загрузка…</p>
          ) : queue ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {(
                [
                  ["В ожидании", queue.pending],
                  ["Выполняется", queue.running],
                  ["Готово", queue.completed],
                  ["Ошибки", queue.failed],
                ] as const
              ).map(([label, count]) => (
                <div key={label} className="rounded-lg bg-genesis-bg p-4 text-center">
                  <div className="text-2xl font-semibold">{count}</div>
                  <div className="text-xs text-genesis-muted">{label}</div>
                </div>
              ))}
            </div>
          ) : null}
        </section>

        <section className="rounded-xl border border-genesis-border bg-genesis-panel p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-genesis-muted">
            Активность
          </h2>
          <ul className="space-y-2">
            {activity.map((event, index) => (
              <li
                key={`${event.at}-${index}`}
                className="flex gap-3 border-b border-genesis-border/50 py-2 text-sm last:border-0"
              >
                <span className="shrink-0 font-mono text-genesis-muted">{event.at}</span>
                <span>{event.message}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="flex flex-wrap justify-center gap-4">
          <button
            type="button"
            onClick={runDemo}
            className="min-w-[160px] rounded-lg border-2 border-genesis-accent bg-genesis-accent/20 px-6 py-3 text-sm font-semibold hover:bg-genesis-accent/40"
          >
            Демо
          </button>
          <button
            type="button"
            onClick={() => control("pause")}
            className="min-w-[120px] rounded-lg bg-yellow-600/80 px-6 py-3 text-sm font-medium hover:bg-yellow-600"
          >
            Пауза
          </button>
          <button
            type="button"
            onClick={() => control("resume")}
            className="min-w-[120px] rounded-lg bg-genesis-green/80 px-6 py-3 text-sm font-medium hover:bg-genesis-green"
          >
            Продолжить
          </button>
        </section>

        {message && (
          <p className="text-center text-sm text-genesis-muted">{message}</p>
        )}
      </div>
    </main>
  );
}
