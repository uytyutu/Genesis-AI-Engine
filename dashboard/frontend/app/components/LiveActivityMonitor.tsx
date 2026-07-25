"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Step = {
  id: string;
  label_ru: string;
  count: number;
  last_at?: string | null;
  status: "success" | "error" | "idle" | "unknown" | string;
  detail_ru?: string;
  display_value?: string;
};

type LiveMonitor = {
  ok?: boolean;
  generated_at?: string;
  window_minutes?: number;
  alive?: boolean;
  headline_ru?: string;
  now?: {
    runner_running?: boolean;
    last_action?: string | null;
    last_message_ru?: string | null;
    last_tick_at?: string | null;
    next_tick_at?: string | null;
    interval_sec?: number;
    ticks?: number;
    session_leads?: number;
    session_drafts?: number;
    session_sends?: number;
    session_skipped?: number;
    current_company?: string | null;
    current_market?: string | null;
    status?: string;
    detail_ru?: string;
  };
  last_10_min?: { steps?: Step[] };
  today?: { steps?: Step[]; kp_sent?: number; stripe_paid_eur?: number };
  queues?: { ready_now?: number; waiting?: number; history?: number };
  reality?: { stripe_paid_total_eur?: number; digistore_commission_eur?: number; rule_ru?: string };
  recent_events?: { at?: string; action?: string; message_ru?: string; status?: string }[];
};

function statusMark(status: string): { mark: string; className: string } {
  if (status === "success") return { mark: "✓", className: "text-emerald-300" };
  if (status === "error") return { mark: "✗", className: "text-rose-300" };
  if (status === "unknown") return { mark: "?", className: "text-amber-200" };
  return { mark: "·", className: "text-white/40" };
}

function fmtTime(iso?: string | null): string {
  if (!iso) return "—";
  const t = String(iso);
  if (t.length >= 16) return t.slice(11, 19);
  return t;
}

function StepList({ steps, title }: { steps: Step[]; title: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/25 p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-white/70">{title}</h3>
      <ul className="mt-3 space-y-2">
        {steps.map((s) => {
          const { mark, className } = statusMark(s.status);
          const value =
            s.display_value ??
            (s.id === "paid" ? s.detail_ru?.split(" ")[0] ?? String(s.count) : String(s.count));
          return (
            <li key={s.id} className="flex items-start justify-between gap-3 text-sm">
              <div className="min-w-0">
                <p className="text-white/90">
                  <span className={`mr-1.5 font-semibold ${className}`}>{mark}</span>
                  {s.label_ru}:{" "}
                  <span className="font-semibold tabular-nums text-white">{value}</span>
                </p>
                {s.detail_ru && s.id !== "paid" ? (
                  <p className="mt-0.5 text-[11px] text-genesis-muted">{s.detail_ru}</p>
                ) : null}
              </div>
              <div className="shrink-0 text-right text-[11px] text-genesis-muted">
                <p className="tabular-nums">{fmtTime(s.last_at)}</p>
                <p className={className}>{s.status}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function LiveActivityMonitor({ pollMs = 10000 }: { pollMs?: number }) {
  const [data, setData] = useState<LiveMonitor | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      let res = await fetch(`${API}/api/farm/live-monitor?window_minutes=10`);
      if (!res.ok) {
        res = await fetch(`${API}/api/acquisition/live-monitor?window_minutes=10`);
      }
      if (!res.ok) {
        setErr(`Live Monitor ${res.status}`);
        return;
      }
      setData(await res.json());
      setErr("");
    } catch {
      setErr("Backend недоступен — Genesis.exe → Запустить.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), Math.max(5000, pollMs));
    return () => window.clearInterval(id);
  }, [load, pollMs]);

  const now = data?.now;
  const alive = Boolean(data?.alive);

  return (
    <section className="rounded-2xl border border-sky-500/30 bg-gradient-to-br from-sky-950/40 via-genesis-panel to-genesis-bg p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-sky-300/80">Live Monitor</p>
          <h2 className="mt-1 text-lg font-semibold text-white">
            {data?.headline_ru ?? "Живая работа системы"}
          </h2>
          <p className="mt-1 text-xs text-genesis-muted">
            Не карточки возможностей — только факты за последние {data?.window_minutes ?? 10} мин и
            сегодня. 0 = реально ноль, не «ещё не подключили».
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full border px-2.5 py-1 text-[11px] ${
              alive
                ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-100"
                : "border-amber-400/40 bg-amber-500/10 text-amber-100"
            }`}
          >
            {alive ? "● жива" : "○ нет тиков"}
          </span>
          <button
            type="button"
            onClick={() => void load()}
            disabled={busy}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs text-white/90 hover:bg-white/10 disabled:opacity-50"
          >
            {busy ? "…" : "Обновить"}
          </button>
        </div>
      </div>

      {err ? <p className="mt-3 text-xs text-amber-200">{err}</p> : null}

      {now ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-white/10 bg-black/30 p-3">
            <p className="text-[10px] uppercase text-white/45">Сейчас делает</p>
            <p className="mt-1 text-sm font-medium text-white">
              {now.runner_running ? now.last_action || "тик" : "остановлен"}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted line-clamp-2">
              {now.detail_ru || now.last_message_ru || "—"}
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 p-3">
            <p className="text-[10px] uppercase text-white/45">Фокус</p>
            <p className="mt-1 text-sm font-medium text-white truncate">
              {now.current_company || "— нет активной компании"}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted">
              {now.current_market || "—"} · тик {fmtTime(now.last_tick_at)} · интервал{" "}
              {now.interval_sec ?? "—"}с
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 p-3">
            <p className="text-[10px] uppercase text-white/45">Сессия runner</p>
            <p className="mt-1 text-sm font-medium text-white tabular-nums">
              send {now.session_sends ?? 0} · skip {now.session_skipped ?? 0}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted tabular-nums">
              leads {now.session_leads ?? 0} · drafts {now.session_drafts ?? 0} · ticks{" "}
              {now.ticks ?? 0}
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 p-3">
            <p className="text-[10px] uppercase text-white/45">Очередь</p>
            <p className="mt-1 text-sm font-medium text-white tabular-nums">
              Ready {data?.queues?.ready_now ?? 0} · Waiting {data?.queues?.waiting ?? 0}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Stripe всего: {data?.reality?.stripe_paid_total_eur?.toFixed(2) ?? "0.00"} € · Digistore:{" "}
              {data?.reality?.digistore_commission_eur?.toFixed(2) ?? "0.00"} €
            </p>
          </div>
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <StepList
          title={`Последние ${data?.window_minutes ?? 10} минут`}
          steps={data?.last_10_min?.steps ?? []}
        />
        <StepList title="Сегодня" steps={data?.today?.steps ?? []} />
      </div>

      {data?.recent_events && data.recent_events.length > 0 ? (
        <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-white/70">
            Последние действия runner
          </h3>
          <ul className="mt-2 max-h-40 space-y-1.5 overflow-y-auto text-xs">
            {data.recent_events.map((e, i) => {
              const { mark, className } = statusMark(e.status || "idle");
              return (
                <li key={`${e.at}-${i}`} className="flex justify-between gap-2">
                  <span className="min-w-0 truncate text-white/85">
                    <span className={`mr-1 ${className}`}>{mark}</span>
                    {e.action}: {e.message_ru}
                  </span>
                  <span className="shrink-0 tabular-nums text-genesis-muted">{fmtTime(e.at)}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {data?.reality?.rule_ru ? (
        <p className="mt-3 text-[11px] text-genesis-muted">{data.reality.rule_ru}</p>
      ) : null}
      {data?.generated_at ? (
        <p className="mt-1 text-[10px] text-white/30">обновлено {fmtTime(data.generated_at)} UTC</p>
      ) : null}
    </section>
  );
}
