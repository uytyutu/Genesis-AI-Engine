import Link from "next/link";
import { BRAND_NAME } from "../lib/publicBrand";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type CursorTask = {
  task_id: string;
  state: string;
  state_label: string;
  progress_percent: number | null;
  progress_label?: string | null;
  progress_is_estimated?: boolean;
  task_note?: string | null;
};

type CursorStatus = {
  status_icon: string;
  status_label: string;
  label: string;
};

export function CursorWorkspacePanel({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<CursorStatus | null>(null);
  const [task, setTask] = useState<CursorTask | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [st, tk] = await Promise.all([
        fetch(`${API}/api/cursor/status`).then((r) => (r.ok ? r.json() : null)),
        fetch(`${API}/api/cursor/task/active`).then((r) => (r.ok ? r.json() : null)),
      ]);
      if (st) setStatus(st);
      setTask(tk?.task ?? null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 12000);
    return () => clearInterval(t);
  }, [refresh]);

  const outcome =
    task?.state === "ready" ? "success" : task?.state === "failed" ? "error" : null;

  return (
    <section className="genesis-card animate-fade-up p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold">⚙️ Работа с Cursor</p>
          <p className="mt-1 text-xs text-genesis-muted">Внутренний инженер — вы управляете через {BRAND_NAME}</p>
        </div>
        <Link
          href="/cursor"
          className="shrink-0 rounded-lg bg-genesis-elevated px-3 py-1.5 text-xs font-medium ring-1 ring-genesis-border hover:ring-genesis-accent/40"
        >
          Открыть →
        </Link>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-genesis-muted">Загрузка статуса…</p>
      ) : (
        <div className="mt-4 space-y-3">
          {status && (
            <p className="flex items-center gap-2 text-sm">
              <span>{status.status_icon}</span>
              <span className="font-medium">{status.status_label}</span>
              <span className="text-genesis-muted">· {status.label}</span>
            </p>
          )}

          {task ? (
            <div
              className={`rounded-xl border px-4 py-3 text-sm ${
                outcome === "success"
                  ? "border-emerald-500/30 bg-emerald-950/20"
                  : outcome === "error"
                    ? "border-red-500/30 bg-red-950/20"
                    : "border-genesis-border bg-genesis-bg/40"
              }`}
            >
              <p className="font-medium">{task.progress_label ?? task.state_label}</p>
              {task.task_note && !compact && (
                <p className="mt-1 text-xs text-genesis-muted line-clamp-2">{task.task_note}</p>
              )}
              {task.progress_percent != null && !task.progress_is_estimated && (
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-genesis-border">
                  <div
                    className={`h-full rounded-full transition-all ${
                      outcome === "error" ? "bg-red-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${task.progress_percent}%` }}
                  />
                </div>
              )}
              {task.progress_is_estimated && (
                <p className="mt-2 text-xs text-genesis-muted">
                  Ожидание ваших действий в Cursor — процент не отображается до проверки.
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-genesis-muted">Нет активных задач — отправьте новую из раздела Cursor.</p>
          )}
        </div>
      )}
    </section>
  );
}
