"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { GenesisCard } from "../components/GenesisCard";
import { formatApiDetail } from "../lib/formatApiError";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type CursorTaskStep = { id: string; label: string; done: boolean; active: boolean };

type CursorTask = {
  task_id: string;
  state: string;
  state_label: string;
  progress_percent: number | null;
  progress_label?: string | null;
  progress_is_estimated?: boolean;
  steps: CursorTaskStep[];
  cursor_opened?: boolean;
  cursor_message?: string | null;
  verify_summary?: string | null;
  task_note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

type CursorStatus = {
  mode: string;
  bridge_ready: boolean;
  label: string;
  status_icon: string;
  status_label: string;
  hint: string;
  cursor_cli_available?: boolean;
  active_task_id?: string | null;
};

type HistoryItem = {
  at: string | null;
  kind: string | null;
  task_note: string | null;
  chars: number | null;
};

const KIND_LABELS: Record<string, string> = {
  task: "Задача",
  status: "Статус",
  verify: "Проверка",
  apply: "Перед применением",
};

function formatWhen(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function CursorPage() {
  const [status, setStatus] = useState<CursorStatus | null>(null);
  const [task, setTask] = useState<CursorTask | null>(null);
  const [queue, setQueue] = useState<CursorTask[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [prompt, setPrompt] = useState("");
  const [taskNote, setTaskNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const refreshTask = useCallback(async () => {
    try {
      const [activeRes, tasksRes, histRes] = await Promise.all([
        fetch(`${API}/api/cursor/task/active`),
        fetch(`${API}/api/cursor/tasks`),
        fetch(`${API}/api/cursor/history`),
      ]);
      if (activeRes.ok) {
        const data = await activeRes.json();
        setTask(data.task ?? null);
      }
      if (tasksRes.ok) {
        const data = await tasksRes.json();
        setQueue(data.tasks ?? []);
      }
      if (histRes.ok) {
        const data = await histRes.json();
        setHistory(data.items ?? []);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/cursor/status`);
      if (res.ok) setStatus(await res.json());
      await refreshTask();
    } catch {
      setMessage("Запустите Genesis с рабочего стола.");
    } finally {
      setLoading(false);
    }
  }, [refreshTask]);

  const loadLast = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/cursor/last`);
      if (res.ok) {
        const data = await res.json();
        if (data?.prompt) setPrompt(data.prompt);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadStatus();
    loadLast();
  }, [loadStatus, loadLast]);

  useEffect(() => {
    if (!task || task.state === "ready" || task.state === "failed") return;
    const t = setInterval(refreshTask, 5000);
    return () => clearInterval(t);
  }, [task, refreshTask]);

  async function handoff(kind: string) {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/cursor/handoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          task_note: taskNote.trim() || null,
          auto_open: kind === "task",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(data.detail));
        return;
      }
      setPrompt(data.prompt);
      if (data.task) setTask(data.task);
      await loadStatus();
      await refreshTask();
      try {
        await navigator.clipboard.writeText(data.prompt);
        setMessage(data.copied_hint ?? `✓ Промпт скопирован (${data.chars} символов).`);
      } catch {
        setMessage(data.copied_hint ?? "Промпт готов — скопируйте вручную.");
      }
    } catch {
      setMessage("Не удалось связаться с Genesis API.");
    } finally {
      setBusy(false);
    }
  }

  async function verifyResult() {
    setBusy(true);
    setMessage("Проверка: pytest + System Check…");
    try {
      const res = await fetch(`${API}/api/cursor/task/verify`, { method: "POST" });
      const data = await res.json();
      if (data.task) setTask(data.task);
      setMessage(data.ok ? `✔ ${data.message}` : `✘ ${data.message}`);
      if (data.verify_summary) {
        setMessage((m) => `${m}\n\n${data.verify_summary}`);
      }
      await loadStatus();
      await refreshTask();
    } catch {
      setMessage("Не удалось запустить проверку.");
    } finally {
      setBusy(false);
    }
  }

  function openCursor() {
    window.open("cursor://", "_self");
    setMessage("Откройте чат Cursor и вставьте промпт (Ctrl+V), если ещё не вставили.");
  }

  const outcome =
    task?.state === "ready" ? "success" : task?.state === "failed" ? "error" : "active";

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-5">
        <header className="genesis-glass p-6 text-center">
          <p className="genesis-label">R0.5 · Инженер за кулисами</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">Работа с Cursor</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Вы работаете в Genesis — Cursor получает контекст, задачу и проверку автоматически.
          </p>
          {status && (
            <p className="mt-4 inline-flex flex-wrap items-center justify-center gap-2 rounded-full border border-genesis-border bg-genesis-panel/80 px-4 py-1.5 text-sm">
              <span>{status.status_icon}</span>
              <span className="font-medium">{status.status_label}</span>
              <span className="text-genesis-muted">· {status.label}</span>
            </p>
          )}
        </header>

        {loading ? (
          <p className="text-center text-sm text-genesis-muted">Загрузка…</p>
        ) : (
          task && (
            <GenesisCard
              title="Текущая задача"
              subtitle={task.progress_label ?? task.state_label}
            >
              <div
                className={`mb-4 rounded-xl border px-4 py-3 text-sm ${
                  outcome === "success"
                    ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                    : outcome === "error"
                      ? "border-red-500/30 bg-red-950/20 text-red-200"
                      : "border-genesis-border bg-genesis-bg/30"
                }`}
              >
                {outcome === "success" && "✔ Выполнено — проверка пройдена"}
                {outcome === "error" && "✘ Ошибка — см. журнал проверки ниже"}
                {outcome === "active" && (task.progress_label ?? "Задача в работе")}
              </div>

              {task.progress_percent != null && !task.progress_is_estimated && (
                <div className="mb-4 h-2 overflow-hidden rounded-full bg-genesis-border">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      outcome === "error"
                        ? "bg-red-500"
                        : "bg-gradient-to-r from-genesis-accent to-violet-500"
                    }`}
                    style={{ width: `${task.progress_percent}%` }}
                  />
                </div>
              )}

              <ul className="space-y-2 text-sm">
                {task.steps.map((step) => (
                  <li
                    key={step.id}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 ${
                      step.active ? "border border-genesis-accent/40 bg-genesis-accent/10" : ""
                    }`}
                  >
                    <span className="text-base">{step.done ? "✓" : step.active ? "●" : "○"}</span>
                    <span className={step.done ? "text-genesis-muted line-through" : ""}>
                      {step.label}
                    </span>
                  </li>
                ))}
              </ul>

              {task.task_note && (
                <p className="mt-3 text-xs text-genesis-muted">
                  <span className="genesis-label">Задача</span>
                  <br />
                  {task.task_note}
                </p>
              )}
              {task.cursor_message && (
                <p className="mt-2 text-xs text-genesis-muted">{task.cursor_message}</p>
              )}
              {task.verify_summary && (
                <pre className="mt-3 max-h-48 overflow-auto rounded-lg bg-genesis-bg p-3 text-xs text-genesis-muted">
                  {task.verify_summary}
                </pre>
              )}
            </GenesisCard>
          )
        )}

        <div className="grid gap-5 lg:grid-cols-2">
          <GenesisCard title="Очередь задач" subtitle={`${queue.length} в журнале`}>
            {queue.length === 0 ? (
              <p className="text-sm text-genesis-muted">Пока нет задач — отправьте первую ниже.</p>
            ) : (
              <ul className="max-h-56 space-y-2 overflow-auto text-sm">
                {queue.map((t) => (
                  <li
                    key={t.task_id}
                    className="flex items-start justify-between gap-2 rounded-lg border border-genesis-border/60 bg-genesis-bg/30 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium">{t.task_note || t.state_label}</p>
                      <p className="text-xs text-genesis-muted">{formatWhen(t.updated_at ?? t.created_at)}</p>
                    </div>
                    <span
                      className={`shrink-0 text-xs ${
                        t.state === "ready"
                          ? "text-emerald-400"
                          : t.state === "failed"
                            ? "text-red-400"
                            : "text-amber-300"
                      }`}
                    >
                      {t.state === "ready" ? "✔" : t.state === "failed" ? "✘" : "…"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </GenesisCard>

          <GenesisCard title="Журнал передач" subtitle="История промптов в Genesis">
            {history.length === 0 ? (
              <p className="text-sm text-genesis-muted">Пока пусто.</p>
            ) : (
              <ul className="max-h-56 space-y-2 overflow-auto text-sm">
                {history.map((h, i) => (
                  <li
                    key={`${h.at}-${i}`}
                    className="rounded-lg border border-genesis-border/60 bg-genesis-bg/30 px-3 py-2"
                  >
                    <p className="font-medium">{KIND_LABELS[h.kind ?? ""] ?? h.kind}</p>
                    <p className="text-xs text-genesis-muted">
                      {formatWhen(h.at)}
                      {h.chars ? ` · ${h.chars} симв.` : ""}
                    </p>
                    {h.task_note && (
                      <p className="mt-1 truncate text-xs text-genesis-muted">{h.task_note}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </GenesisCard>
        </div>

        <GenesisCard title="Новая задача" subtitle="Контекст проекта подставится автоматически">
          <textarea
            value={taskNote}
            onChange={(e) => setTaskNote(e.target.value)}
            rows={4}
            placeholder="Например: исправить страницу продукта / добавить панель решений…"
            className="w-full rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm outline-none focus:border-genesis-accent"
          />
          <p className="mt-2 text-xs text-genesis-muted">
            Genesis добавит PROJECT_STATE, Roadmap, Factory, финансы и память владельца.
          </p>
        </GenesisCard>

        <div className="grid gap-2 sm:grid-cols-2">
          <ActionButton
            disabled={busy}
            onClick={() => handoff("task")}
            icon="📤"
            label="Отправить задачу"
            sub="Промпт + буфер + Cursor"
          />
          <ActionButton
            disabled={busy}
            onClick={verifyResult}
            icon="🔄"
            label="Проверить результат"
            sub="pytest + System Check"
          />
          <ActionButton
            disabled={busy}
            onClick={() => handoff("status")}
            icon="📋"
            label="Скопировать статус"
            sub="Контекст без новой задачи"
          />
          <ActionButton
            disabled={busy}
            onClick={() => handoff("apply")}
            icon="✅"
            label="Перед применением"
            sub="Чеклист владельца"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={openCursor}
            className="rounded-xl border border-genesis-accent/40 bg-genesis-accent/10 px-4 py-2 text-sm font-medium hover:bg-genesis-accent/20"
          >
            Открыть Cursor
          </button>
        </div>

        {message && (
          <p className="whitespace-pre-wrap rounded-xl border border-genesis-border bg-genesis-bg/60 px-4 py-3 text-sm text-genesis-muted">
            {message}
          </p>
        )}

        {status?.hint && (
          <p className="text-center text-xs text-genesis-muted">{status.hint}</p>
        )}

        {prompt && (
          <GenesisCard title="Последний промпт" subtitle={`${prompt.length} символов`}>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-xl bg-genesis-bg p-4 text-xs leading-relaxed text-genesis-muted">
              {prompt}
            </pre>
          </GenesisCard>
        )}

        <p className="text-center text-sm">
          <Link href="/" className="text-genesis-accent hover:underline">
            ← Mission Control
          </Link>
        </p>
      </div>
    </main>
  );
}

function ActionButton({
  icon,
  label,
  sub,
  onClick,
  disabled,
}: {
  icon: string;
  label: string;
  sub: string;
  onClick: () => void;
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="rounded-2xl border border-genesis-border bg-genesis-panel/80 p-4 text-left transition hover:border-genesis-accent/40 disabled:opacity-50"
    >
      <span className="text-xl">{icon}</span>
      <p className="mt-2 font-semibold">{label}</p>
      <p className="mt-1 text-xs text-genesis-muted">{sub}</p>
    </button>
  );
}
