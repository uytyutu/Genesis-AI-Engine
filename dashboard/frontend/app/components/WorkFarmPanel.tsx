"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type WorkType = {
  id: string;
  enabled?: boolean;
  label_ru?: string;
  note_ru?: string;
  ai_share_pct?: number;
};

type RecentJob = {
  job_id?: string;
  order_id?: string;
  work_type?: string;
  status?: string;
  at?: string;
  product_id?: string;
};

type LandingStats = {
  received?: number;
  success?: number;
  error?: number;
  avg_duration_min?: number | null;
  avg_revenue_eur?: number | null;
  avg_cost_eur_proxy?: number | null;
  sample_note_ru?: string;
  cost_source?: string;
};

type ReplayStep = {
  id?: string;
  status?: string;
  duration_sec?: number;
  worker?: string;
  module?: string | null;
  manual_review?: boolean;
  detail_ru?: string;
  cost_eur_proxy?: number | null;
};

type Replay = {
  headline_ru?: string;
  job_id?: string;
  order_id?: string;
  status?: string;
  steps?: ReplayStep[];
  modules_used?: string[];
  had_manual_review?: boolean;
  duration_sec?: number;
  economics?: {
    revenue_eur?: number;
    cost_eur_proxy?: number;
    margin_eur_proxy?: number;
    cost_note_ru?: string;
  };
  note_ru?: string;
};

type Board = {
  headline_ru?: string;
  primary_work_type?: string;
  marketplace?: boolean;
  recent_jobs?: RecentJob[];
  stats?: { landing_page?: LandingStats };
  catalog?: { work_types?: WorkType[]; pipeline_ru?: string[]; rule_ru?: string };
};

function fmtEur(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n.toFixed(2)} €`;
}

export function WorkFarmPanel() {
  const [board, setBoard] = useState<Board | null>(null);
  const [err, setErr] = useState("");
  const [replay, setReplay] = useState<Replay | null>(null);
  const [replayBusy, setReplayBusy] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/work-farm/status`);
      if (!res.ok) {
        setErr(`Work Farm ${res.status}`);
        return;
      }
      setBoard(await res.json());
      setErr("");
    } catch {
      setErr("Work Farm недоступна — перезапустите Genesis.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openReplay = async (jobId: string) => {
    if (!jobId) return;
    setReplayBusy(jobId);
    try {
      const res = await fetch(`${API}/api/work-farm/replay/${encodeURIComponent(jobId)}`);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErr(body.detail || `Replay ${res.status}`);
        return;
      }
      setReplay(body as Replay);
      setErr("");
    } catch {
      setErr("Replay не загрузился");
    } finally {
      setReplayBusy("");
    }
  };

  const types = board?.catalog?.work_types ?? [];
  const recent = board?.recent_jobs ?? [];
  const st = board?.stats?.landing_page;

  return (
    <section className="rounded-2xl border border-violet-500/25 bg-violet-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-violet-300/80">Work Farm v0</p>
          <h2 className="mt-1 text-sm font-semibold text-white">
            {board?.headline_ru ?? "Stripe → Landing → Quality Gate"}
          </h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            {board?.catalog?.rule_ru ??
              "Собственные оплаченные заказы. Marketplace = false."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs text-white/90 hover:bg-white/10"
        >
          Обновить
        </button>
      </div>

      {err ? <p className="mt-2 text-xs text-amber-200">{err}</p> : null}

      <div className="mt-4 rounded-xl border border-white/10 bg-black/25 p-4">
        <p className="text-[10px] uppercase tracking-wide text-violet-200/80">Landing jobs</p>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          <Stat label="Получено" value={String(st?.received ?? 0)} />
          <Stat label="Успешно" value={String(st?.success ?? 0)} ok />
          <Stat label="Ошибка" value={String(st?.error ?? 0)} warn={(st?.error ?? 0) > 0} />
          <Stat
            label="Среднее время"
            value={st?.avg_duration_min != null ? `${st.avg_duration_min} мин` : "—"}
          />
          <Stat label="Средняя прибыль" value={fmtEur(st?.avg_revenue_eur)} />
          <Stat label="Средняя себестоимость" value={fmtEur(st?.avg_cost_eur_proxy)} />
        </div>
        <p className="mt-2 text-[10px] text-genesis-muted">
          {st?.sample_note_ru ||
            "Себестоимость — прокси до учёта токенов. 0 = ещё нет реальных jobs."}
        </p>
      </div>

      {board?.catalog?.pipeline_ru?.length ? (
        <p className="mt-3 text-[11px] text-violet-100/80">
          {board.catalog.pipeline_ru.join(" → ")}
        </p>
      ) : null}

      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {types.map((t) => (
          <li
            key={t.id}
            className={`rounded-lg border px-3 py-2 text-xs ${
              t.enabled
                ? "border-emerald-500/30 bg-emerald-950/20"
                : "border-white/10 bg-black/20"
            }`}
          >
            <p className="font-medium text-white">
              {t.enabled ? "✓" : "○"} {t.label_ru || t.id}
            </p>
            <p className="mt-1 text-genesis-muted">{t.note_ru}</p>
          </li>
        ))}
      </ul>

      <div className="mt-4">
        <p className="text-[10px] uppercase tracking-wide text-white/45">Последние jobs · Replay</p>
        {!recent.length ? (
          <p className="mt-2 text-xs text-genesis-muted">
            Пока пусто — job появится после оплаты Stripe (Landing).
          </p>
        ) : (
          <ul className="mt-2 max-h-48 space-y-1.5 overflow-y-auto text-xs">
            {recent.map((j, i) => (
              <li
                key={`${j.job_id}-${i}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-white/5 bg-black/20 px-2 py-1.5"
              >
                <span className="min-w-0 truncate text-white/85">
                  {j.work_type} · {j.order_id} · {j.status}
                </span>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="tabular-nums text-genesis-muted">
                    {String(j.at || "").slice(11, 19) || "—"}
                  </span>
                  {j.job_id ? (
                    <button
                      type="button"
                      disabled={replayBusy === j.job_id}
                      onClick={() => void openReplay(j.job_id!)}
                      className="rounded border border-violet-400/40 bg-violet-950/40 px-2 py-0.5 text-[10px] text-violet-100 hover:bg-violet-900/50 disabled:opacity-50"
                    >
                      {replayBusy === j.job_id ? "…" : "Replay Job"}
                    </button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {replay ? (
        <div className="mt-4 rounded-xl border border-sky-500/25 bg-sky-950/20 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-wide text-sky-200/80">Replay Job</p>
              <p className="mt-1 text-sm font-medium text-white">{replay.headline_ru}</p>
              <p className="mt-1 text-[11px] text-genesis-muted">
                {replay.order_id} · {replay.status} ·{" "}
                {replay.duration_sec != null ? `${replay.duration_sec}s` : "—"}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setReplay(null)}
              className="text-xs text-genesis-muted hover:text-white"
            >
              ✕
            </button>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-3 text-xs">
            <p className="rounded border border-white/10 bg-black/20 px-2 py-1.5">
              Выручка: <span className="text-emerald-200">{fmtEur(replay.economics?.revenue_eur)}</span>
            </p>
            <p className="rounded border border-white/10 bg-black/20 px-2 py-1.5">
              Себестоимость:{" "}
              <span className="text-amber-100">{fmtEur(replay.economics?.cost_eur_proxy)}</span>
            </p>
            <p className="rounded border border-white/10 bg-black/20 px-2 py-1.5">
              Маржа (прокси):{" "}
              <span className="text-white">{fmtEur(replay.economics?.margin_eur_proxy)}</span>
            </p>
          </div>
          {replay.modules_used?.length ? (
            <p className="mt-2 text-[11px] text-genesis-muted">
              Модули: {replay.modules_used.join(" · ")}
              {replay.had_manual_review ? " · была ручная проверка" : ""}
            </p>
          ) : null}
          <ul className="mt-3 space-y-1.5 text-xs">
            {(replay.steps || []).map((s) => (
              <li
                key={s.id}
                className="flex justify-between gap-2 rounded border border-white/5 bg-black/25 px-2 py-1.5"
              >
                <span className="min-w-0">
                  <span className="font-medium text-white">{s.id}</span>
                  <span className="text-genesis-muted">
                    {" "}
                    · {s.status} · {s.module || s.worker || "—"}
                    {s.manual_review ? " · manual" : ""}
                  </span>
                  {s.detail_ru ? (
                    <span className="mt-0.5 block truncate text-genesis-muted">{s.detail_ru}</span>
                  ) : null}
                </span>
                <span className="shrink-0 tabular-nums text-sky-100/80">
                  {s.duration_sec != null ? `${s.duration_sec}s` : "—"}
                </span>
              </li>
            ))}
          </ul>
          {replay.economics?.cost_note_ru ? (
            <p className="mt-2 text-[10px] text-genesis-muted">{replay.economics.cost_note_ru}</p>
          ) : null}
          {replay.note_ru ? (
            <p className="mt-1 text-[10px] text-white/40">{replay.note_ru}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function Stat({
  label,
  value,
  ok,
  warn,
}: {
  label: string;
  value: string;
  ok?: boolean;
  warn?: boolean;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/30 px-2.5 py-2">
      <p className="text-[10px] uppercase text-white/45">{label}</p>
      <p
        className={`mt-1 text-sm font-semibold tabular-nums ${
          warn ? "text-amber-200" : ok ? "text-emerald-200" : "text-white"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
