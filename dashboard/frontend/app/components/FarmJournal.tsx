"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";
import { fetchApi } from "../lib/fetchApi";
import {
  FarmTaskEvent,
  PayoutGuide,
  lifecycleRowClass,
  lifecycleTitle,
  showPayAmount,
  taskTone,
} from "../lib/farmLifecycleUi";
import { MoneyMonitorPanel, type MoneyMonitorData } from "./MoneyMonitorPanel";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function farmList<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

type FarmDash = {
  owner_name: string;
  running: boolean;
  workers_active: number;
  today_earned_eur: number;
  total_earned_eur: number;
  total_tasks_done: number;
  net_profit_eur: number;
  llm_cost_eur?: number;
  last_tick_at: string | null;
  recent_tasks: FarmTaskEvent[];
  balance_label: string;
  sandbox: boolean;
  dry_run?: { active: boolean; streak: number; total_potential_eur: number };
  payment_monitor?: {
    monitor?: {
      toloka?: { connected?: boolean; live_tasks?: boolean; task_count?: number };
      scale?: { connected?: boolean };
    };
  };
  last_live_connection_test?: { ok: boolean; log_line?: string };
  payout_guide?: PayoutGuide;
  money_monitor?: MoneyMonitorData;
  global_spider?: {
    polling_interval_sec?: number;
    min_task_price?: number;
  };
};

const ADAPTER_LABELS: Record<string, string> = {
  ai_labeling: "AI-разметка",
  data_clean: "Чистка данных",
  text_classify: "Классификация",
  record_verify: "Проверка",
  scale_ai_probe: "Scale (проверка)",
  toloka_probe: "Toloka (проверка)",
  toloka_submit: "Toloka (отправка)",
  dry_run: "DRY RUN",
  farm_tick: "Цикл фермы",
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function FarmJournal() {
  const [dash, setDash] = useState<FarmDash | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pulse, setPulse] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchApi(`${API}/api/farm/dashboard/lite`, { timeoutMs: 12_000 });
      if (!res.ok) throw new Error("dashboard");
      setDash(await res.json());
      setError("");
      setPulse((p) => p + 1);
    } catch {
      setError("Backend не отвечает. Откройте Genesis.exe → Запустить → дождитесь «✔ Готов».");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const refreshMs = dash?.running ? 3000 : 5000;
    const id = window.setInterval(refresh, refreshMs);
    return () => window.clearInterval(id);
  }, [refresh, dash?.running]);

  const pollSec = Math.max(5, dash?.global_spider?.polling_interval_sec ?? 8);

  useEffect(() => {
    if (!dash?.running) return;
    const tick = window.setInterval(async () => {
      try {
        await fetchApi(`${API}/api/farm/feed`, { method: "POST", timeoutMs: 8_000 });
        await refresh();
      } catch {
        /* background */
      }
    }, pollSec * 1000);
    return () => window.clearInterval(tick);
  }, [dash?.running, refresh, pollSec]);

  const guide = dash?.payout_guide;

  return (
    <main className="min-h-screen pb-16">
      <div className="mx-auto max-w-4xl space-y-6 px-4 pt-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/90">Журнал · live</p>
            <h1 className="mt-2 text-3xl font-bold text-white">Доход и задачи фермы</h1>
            <p className="mt-2 text-sm text-genesis-muted">
              Обновление каждые {dash?.running ? "3" : "5"} сек
              {dash?.running && dash.global_spider?.polling_interval_sec
                ? ` · охота каждые ${dash.global_spider.polling_interval_sec} сек`
                : ""}
              {dash?.global_spider?.min_task_price != null
                ? ` · фильтр ≥ ${dash.global_spider.min_task_price.toFixed(2)} €`
                : ""}
              {dash?.last_tick_at ? ` · последний tick ${formatTime(dash.last_tick_at)}` : ""}
              {pulse > 0 ? ` · #${pulse}` : ""}
            </p>
          </div>
          <Link
            href="/"
            className="rounded-xl border border-genesis-border px-4 py-2 text-sm text-white hover:bg-genesis-elevated/40"
          >
            ← Цифровая ферма
          </Link>
        </header>

        {error ? (
          <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-sm text-rose-200 space-y-2">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => {
                setLoading(true);
                void refresh();
              }}
              className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs text-rose-100 hover:bg-rose-950/40"
            >
              Повторить
            </button>
          </div>
        ) : null}

        {dash ? (
          <>
            <MoneyMonitorPanel data={dash.money_monitor} compact />

            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="genesis-card border-emerald-500/30 bg-emerald-950/15 p-4">
                <p className="text-xs text-emerald-200/70">Сегодня</p>
                <p className="mt-1 text-2xl font-bold text-emerald-200">
                  {formatEur(dash.today_earned_eur)}
                </p>
              </div>
              <div className="genesis-card p-4">
                <p className="text-xs text-genesis-muted">Всего накоплено</p>
                <p className="mt-1 text-2xl font-bold text-white">{formatEur(dash.total_earned_eur)}</p>
                <p className="mt-1 text-[11px] text-genesis-muted">{dash.balance_label}</p>
              </div>
              <div className="genesis-card p-4">
                <p className="text-xs text-genesis-muted">Чистая прибыль сегодня</p>
                <p className="mt-1 text-2xl font-bold text-white">{formatEur(dash.net_profit_eur)}</p>
                {dash.llm_cost_eur != null ? (
                  <p className="mt-1 text-[11px] text-genesis-muted">
                    Расход ИИ: {formatEur(dash.llm_cost_eur)}
                  </p>
                ) : null}
              </div>
              <div className="genesis-card p-4">
                <p className="text-xs text-genesis-muted">Статус</p>
                <p
                  className={`mt-1 text-lg font-bold ${dash.running ? "text-emerald-300" : "text-genesis-muted"}`}
                >
                  {dash.running ? `${dash.workers_active} комбайнов · RUN` : "Остановлена"}
                </p>
                <p className="mt-1 text-[11px] text-genesis-muted">{dash.total_tasks_done} задач всего</p>
              </div>
            </section>

            {guide ? (
              <section className="genesis-card border-violet-500/25 bg-violet-950/10 p-5">
                <h2 className="text-sm font-semibold text-white">{guide.title}</h2>
                <p className="mt-1 text-[11px] text-genesis-muted">
                  Порог алерта ≈ ${guide.threshold_usd.toFixed(0)} · {guide.note}
                </p>
                <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-white/90">
                  {farmList(guide.steps).map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </section>
            ) : null}

            {dash.dry_run?.active ? (
              <section className="genesis-card border-sky-500/30 bg-sky-950/15 p-4 text-sm text-sky-100">
                DRY RUN · серия {dash.dry_run.streak} · потенциал{" "}
                {formatEur(dash.dry_run.total_potential_eur)}
              </section>
            ) : null}

            {dash.payment_monitor?.monitor ? (
              <section className="genesis-card p-4 text-xs text-white/85">
                Toloka:{" "}
                {dash.payment_monitor.monitor.toloka?.connected ? "🟢 Pipeline OK" : "⚪ нет"} · Scale:{" "}
                {dash.payment_monitor.monitor.scale?.connected ? "🟢 OK" : "⏭ SKIP"}
                {dash.last_live_connection_test ? (
                  <span className="ml-2 text-genesis-muted">
                    · Live test {dash.last_live_connection_test.ok ? "✅" : "❌"}
                  </span>
                ) : null}
              </section>
            ) : null}

            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold text-white">Журнал заработка</h2>
              <p className="mt-1 text-[11px] text-genesis-muted">
                Задача принята → выполнена → платформа подтвердила → баланс вырос
              </p>
              {!farmList(dash.recent_tasks).length ? (
                <p className="mt-4 text-sm text-genesis-muted">
                  Пусто — на{" "}
                  <Link href="/" className="text-emerald-300 underline">
                    ферме
                  </Link>{" "}
                  нажми «Запустить».
                </p>
              ) : (
                <ul className="mt-4 max-h-[32rem] space-y-2 overflow-y-auto text-xs">
                  {farmList(dash.recent_tasks).map((t) => (
                    <li
                      key={t.id}
                      className={`rounded-lg border px-3 py-2.5 ${lifecycleRowClass(t.lifecycle_stage)}`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-white">{lifecycleTitle(t)}</p>
                          <p className="mt-0.5 text-[11px] text-genesis-muted">
                            {formatTime(t.at)} · {ADAPTER_LABELS[t.adapter] ?? t.adapter}
                            {t.target ? ` · ${t.target}` : ""}
                          </p>
                        </div>
                        <span className={taskTone(t)}>
                          {showPayAmount(t) ? `+${t.pay_eur.toFixed(4)} € · ` : ""}
                          {t.detail}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : loading ? (
          <p className="text-sm text-genesis-muted">Загрузка журнала…</p>
        ) : null}
      </div>
    </main>
  );
}
