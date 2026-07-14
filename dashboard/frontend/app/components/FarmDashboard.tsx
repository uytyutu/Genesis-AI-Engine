"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Combiner = { id: string; label: string; pay_eur: number; pay_label: string; primary?: boolean };
type Platform = {
  id: string;
  label: string;
  status: string;
  status_label: string;
  note: string;
  env_var?: string;
  pay_hint?: string;
  signup_url?: string | null;
  steps?: string[];
  connected?: boolean;
};
type ChecklistItem = { step: string; title: string; detail: string };
type TaskEvent = {
  id: string;
  at: string;
  adapter: string;
  pay_eur: number;
  target: string;
  detail: string;
  ok: boolean;
};

type FarmDash = {
  owner_name: string;
  running: boolean;
  workers_active: number;
  workers_target: number;
  today_earned_eur: number;
  total_earned_eur: number;
  total_tasks_done: number;
  net_profit_eur: number;
  available_for_withdraw_eur: number;
  withdraw_min_eur: number;
  sandbox: boolean;
  balance_label: string;
  combiners: Combiner[];
  worker_flow?: { step: number; id: string; title: string; detail: string }[];
  primary_combiner?: string;
  async_concurrency?: number;
  platforms: Platform[];
  ceo_checklist?: ChecklistItem[];
  labels_export_count?: number;
  labels_export_ready?: boolean;
  scale_ai?: {
    connected: boolean;
    configured: boolean;
    status: string;
    status_label: string;
    log_line?: string;
    message?: string;
  };
  priority_manager?: {
    pipeline_parallelism: boolean;
    async_note: string;
    router_note: string;
    cache: { entries: number; max_entries: number };
    learning: {
      total_ops: number;
      min_ops_for_priority: number;
      investor_mode: boolean;
      top_adapter: string | null;
      note: string;
      adapters: { adapter_id: string; eur_per_second: number; cache_rate: number }[];
    };
    cloud_dispatcher?: {
      execution_mode: string;
      local_note: string;
      pool_configured: boolean;
      pool: { ok: boolean; status: string; message: string; pool_url?: string };
    };
  };
  recent_tasks: TaskEvent[];
  honesty_note: string;
  cost_ratio_note: string;
  last_tick_at: string | null;
  revenue_forecast?: {
    disclaimer: string;
    labeling_swarm_10h: { net_eur: number; nodes: number; gross_eur: number };
    labeling_swarm_per_day: { net_eur: number };
    phases: { label: string; eur_per_day: string; note: string }[];
    scaling_note: string;
  };
  last_battle_test?: {
    at: string;
    earned_eur: number;
    tasks_done: number;
    execution_target: string;
    pay_per_task_eur: number;
    tasks_per_hour_est: number;
  };
  prepare_live?: {
    farm_mode: string;
    live_ready: boolean;
    checklist: { step: number; done: boolean; title: string }[];
    next?: string;
  };
};

const ADAPTER_LABELS: Record<string, string> = {
  ai_labeling: "AI-разметка",
  data_clean: "Чистка данных",
  text_classify: "Классификация",
  record_verify: "Проверка",
};

export function FarmDashboard() {
  const [dash, setDash] = useState<FarmDash | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [workers, setWorkers] = useState(10);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/dashboard`);
      if (res.ok) setDash(await res.json());
    } catch {
      setMessage("Не удалось загрузить ферму. Запустите Genesis.exe.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const poll = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(poll);
  }, [refresh]);

  useEffect(() => {
    if (!dash?.running) return;
    const tick = window.setInterval(async () => {
      try {
        await fetch(`${API}/api/farm/tick`, { method: "POST" });
        refresh();
      } catch {
        /* background */
      }
    }, 20_000);
    return () => window.clearInterval(tick);
  }, [dash?.running, refresh]);

  async function startFarm() {
    setBusy("start");
    setMessage("");
    try {
      const feed = await fetch(`${API}/api/farm/feed`, { method: "POST" });
      const feedBody = await feed.json().catch(() => ({}));
      const res = await fetch(`${API}/api/farm/start?workers=${workers}`, { method: "POST" });
      const body = await res.json();
      setMessage(feedBody.message ?? body.message ?? "Ферма запущена");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function stopFarm() {
    setBusy("stop");
    try {
      const res = await fetch(`${API}/api/farm/stop`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Остановлено");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function manualTick() {
    setBusy("tick");
    try {
      const res = await fetch(`${API}/api/farm/tick`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Готово");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runBattleTest() {
    setBusy("battle");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/farm/battle-test`, { method: "POST" });
      const body = await res.json();
      setMessage(body.verdict ?? body.message ?? "Тест завершён");
      refresh();
    } finally {
      setBusy("");
    }
  }

  const connectedPlatforms = dash?.platforms.filter((p) => p.connected).length ?? 0;
  const totalPlatforms = dash?.platforms.length ?? 0;

  return (
    <main className="min-h-screen pb-16">
      <div className="mx-auto max-w-4xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/50 via-genesis-panel to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/90">Virtus Core · Рабочий инструмент</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Цифровая ферма · {dash?.owner_name ?? "…"}</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Одна кнопка — рой комбайнов размечает данные. Биржи подключаешь ты (без твоего ключа Genesis не может
            получать € с Scale/Toloka/MTurk).
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/monitor" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Пульт CEO
            </Link>
            <Link href="/finance" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Деньги
            </Link>
            <a
              href={`${API}/api/farm/export/labels`}
              className="rounded-lg border border-violet-500/40 px-3 py-1.5 text-violet-200 hover:bg-violet-950/30"
            >
              Скачать разметку{dash?.labels_export_count ? ` (${dash.labels_export_count})` : ""}
            </a>
          </div>
        </header>

        {dash?.ceo_checklist && (
          <section className="genesis-card border-amber-500/30 bg-amber-950/15 p-5">
            <h2 className="text-sm font-bold text-amber-100">Что сделать тебе (по порядку)</h2>
            <ol className="mt-3 space-y-3">
              {dash.ceo_checklist.map((item) => (
                <li key={item.step} className="flex gap-3 text-sm">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-500/25 text-xs font-bold text-amber-100">
                    {item.step}
                  </span>
                  <div>
                    <p className="font-medium text-white">{item.title}</p>
                    <p className="text-xs text-amber-100/70">{item.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
            <p className="mt-3 text-[11px] text-amber-200/60">
              Шаблон ключей: dashboard/backend/env.platforms.example → скопируй строки в .env.local
            </p>
            {dash.prepare_live ? (
              <div className="mt-4 rounded-lg border border-emerald-500/25 bg-emerald-950/20 p-3">
                <p className="text-xs font-semibold text-emerald-100">
                  Боевой режим: {dash.prepare_live.farm_mode === "live" ? "LIVE" : "dry_run"}
                </p>
                <ul className="mt-2 space-y-1 text-xs text-emerald-200/80">
                  {dash.prepare_live.checklist.map((c) => (
                    <li key={c.step}>
                      {c.done ? "✓" : "○"} {c.title}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        )}

        {dash?.scale_ai ? (
          <p
            className={`rounded-xl border px-4 py-2 text-xs ${
              dash.scale_ai.connected
                ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                : "border-amber-500/30 bg-amber-950/20 text-amber-100"
            }`}
          >
            {dash.scale_ai.log_line ?? `Scale AI: ${dash.scale_ai.status_label}`}
            {dash.scale_ai.message ? ` — ${dash.scale_ai.message}` : ""}
          </p>
        ) : null}

        {dash?.priority_manager ? (
          <section className="genesis-card border-violet-500/25 bg-violet-950/10 p-5">
            <h2 className="text-sm font-bold text-violet-100">Менеджер приоритетов</h2>
            <p className="mt-1 text-xs text-violet-200/70">{dash.priority_manager.async_note}</p>
            <p className="mt-1 text-xs text-violet-200/70">{dash.priority_manager.router_note}</p>
            <p className="mt-3 text-sm text-white">
              {dash.priority_manager.learning.note}
              {dash.priority_manager.learning.investor_mode && dash.priority_manager.learning.top_adapter
                ? ` · Лидер: ${ADAPTER_LABELS[dash.priority_manager.learning.top_adapter] ?? dash.priority_manager.learning.top_adapter}`
                : ""}
            </p>
            <p className="mt-2 text-xs text-genesis-muted">
              Кэш паттернов: {dash.priority_manager.cache.entries} / {dash.priority_manager.cache.max_entries}
            </p>
            {dash.priority_manager.cloud_dispatcher ? (
              <p className="mt-2 text-xs text-violet-200/80">
                Облако: режим <strong>{dash.priority_manager.cloud_dispatcher.execution_mode}</strong>
                {dash.priority_manager.cloud_dispatcher.pool_configured
                  ? ` · пул ${dash.priority_manager.cloud_dispatcher.pool.ok ? "онлайн" : "offline"}`
                  : " · пульт на ноутбуке (задай FARM_WORKER_POOL_URL для VPS)"}
              </p>
            ) : null}
          </section>
        ) : null}

        {dash?.revenue_forecast ? (
          <section className="genesis-card border-sky-500/20 bg-sky-950/10 p-5">
            <h2 className="text-sm font-bold text-sky-100">Прогноз (математика, не гарантия)</h2>
            <p className="mt-1 text-xs text-sky-200/70">{dash.revenue_forecast.disclaimer}</p>
            <p className="mt-3 text-sm text-white">
              50 нод × 10 ч: ~<strong>{formatEur(dash.revenue_forecast.labeling_swarm_10h.net_eur)}</strong> чистыми
              · сутки: ~<strong>{formatEur(dash.revenue_forecast.labeling_swarm_per_day.net_eur)}</strong>
            </p>
            {dash.last_battle_test ? (
              <p className="mt-2 text-xs text-emerald-200">
                Последний боевой тест: +{dash.last_battle_test.earned_eur.toFixed(4)} € ·{" "}
                {dash.last_battle_test.tasks_done} задач · {dash.last_battle_test.execution_target} · ~
                {dash.last_battle_test.pay_per_task_eur.toFixed(4)} €/задача
              </p>
            ) : null}
            <ul className="mt-3 space-y-1 text-xs text-genesis-muted">
              {dash.revenue_forecast.phases.map((p) => (
                <li key={p.label}>
                  <strong>{p.label}</strong>: {p.eur_per_day} €/день — {p.note}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {dash && (
          <section className="genesis-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs text-genesis-muted">{dash.balance_label}</p>
                <p className="mt-1 text-4xl font-bold tabular-nums text-emerald-300">
                  {formatEur(dash.total_earned_eur)}
                </p>
                <p className="mt-2 text-sm text-white/80">
                  Сегодня: <strong>{formatEur(dash.today_earned_eur)}</strong> · Задач:{" "}
                  <strong>{dash.total_tasks_done}</strong>
                </p>
                <p className="mt-1 text-xs text-genesis-muted">{dash.cost_ratio_note}</p>
              </div>
              <div className="text-right text-xs">
                <p
                  className={`inline-flex rounded-full px-3 py-1 font-semibold ${
                    dash.running ? "bg-emerald-500/20 text-emerald-200" : "bg-white/10 text-genesis-muted"
                  }`}
                >
                  {dash.running ? `${dash.workers_active} комбайнов` : "Остановлена"}
                </p>
                <p className="mt-2 text-genesis-muted">
                  Биржи: {connectedPlatforms}/{totalPlatforms} подключено
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <label className="text-xs text-genesis-muted">
                Комбайнов:
                <input
                  type="number"
                  min={1}
                  max={1000}
                  value={workers}
                  onChange={(e) => setWorkers(Number(e.target.value) || 10)}
                  className="ml-2 w-20 rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1 text-sm text-white"
                />
              </label>
              {!dash.running ? (
                <button
                  type="button"
                  disabled={busy === "start"}
                  onClick={() => void startFarm()}
                  className="rounded-xl bg-emerald-600 px-6 py-3 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
                >
                  {busy === "start" ? "Запуск…" : "▶ Запустить ферму"}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busy === "stop"}
                  onClick={() => void stopFarm()}
                  className="rounded-xl bg-rose-700 px-6 py-3 text-sm font-bold text-white hover:bg-rose-600 disabled:opacity-50"
                >
                  ⏸ Остановить
                </button>
              )}
              <button
                type="button"
                disabled={busy === "battle"}
                onClick={() => void runBattleTest()}
                className="rounded-xl border border-sky-500/40 bg-sky-950/30 px-4 py-3 text-sm font-semibold text-sky-100 hover:bg-sky-900/40 disabled:opacity-50"
              >
                {busy === "battle" ? "Тест…" : "⚡ Боевой тест (1 нода)"}
              </button>
            </div>
            {message ? <p className="mt-4 text-sm text-emerald-200">{message}</p> : null}
          </section>
        )}

        {dash && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold text-white">Биржи разметки (8 площадок)</h2>
            <p className="mt-1 text-xs text-genesis-muted">
              Genesis видит список. Подключение — только после твоей регистрации и ключа в .env.local.
            </p>
            <ul className="mt-4 space-y-4">
              {dash.platforms.map((p) => (
                <li
                  key={p.id}
                  className={`rounded-xl border px-4 py-3 ${
                    p.connected ? "border-emerald-500/30 bg-emerald-950/15" : "border-white/10"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-medium text-white">{p.label}</span>
                    <span className={`text-xs ${p.connected ? "text-emerald-400" : "text-amber-400"}`}>
                      {p.status_label}
                      {p.pay_hint ? ` · ${p.pay_hint}` : ""}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-genesis-muted">{p.note}</p>
                  {p.steps && p.steps.length > 0 && !p.connected ? (
                    <ol className="mt-2 list-decimal space-y-1 pl-4 text-[11px] text-amber-100/80">
                      {p.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  ) : null}
                  {p.env_var && !p.connected ? (
                    <p className="mt-2 font-mono text-[10px] text-violet-200">
                      .env.local → {p.env_var}=твой_ключ
                    </p>
                  ) : null}
                  {p.signup_url && !p.connected ? (
                    <a
                      href={p.signup_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-[11px] text-sky-300 underline"
                    >
                      Открыть регистрацию →
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        )}

        {dash && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold text-white">Последние задачи</h2>
            {!dash.recent_tasks.length ? (
              <p className="mt-3 text-sm text-genesis-muted">Пусто — жми «Запустить ферму».</p>
            ) : (
              <ul className="mt-3 max-h-72 space-y-2 overflow-y-auto text-xs">
                {dash.recent_tasks.map((t) => (
                  <li
                    key={t.id}
                    className="flex flex-wrap justify-between gap-2 rounded-lg border border-white/5 px-3 py-2"
                  >
                    <span className="text-white/90">
                      {ADAPTER_LABELS[t.adapter] ?? t.adapter} · {t.target}
                    </span>
                    <span className={t.ok ? "text-emerald-400" : "text-rose-400"}>
                      +{t.pay_eur.toFixed(2)} € · {t.detail}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {dash ? (
          <p className="text-center text-[11px] leading-relaxed text-genesis-muted">{dash.honesty_note}</p>
        ) : null}
      </div>
    </main>
  );
}
