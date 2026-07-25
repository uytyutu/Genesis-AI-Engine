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

type Board = {
  headline_ru?: string;
  primary_work_type?: string;
  marketplace?: boolean;
  recent_jobs?: RecentJob[];
  catalog?: { work_types?: WorkType[]; pipeline_ru?: string[]; rule_ru?: string };
};

export function WorkFarmPanel() {
  const [board, setBoard] = useState<Board | null>(null);
  const [err, setErr] = useState("");

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

  const types = board?.catalog?.work_types ?? [];
  const recent = board?.recent_jobs ?? [];

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
              "Собственные оплаченные заказы. Marketplace внешних задач — позже."}
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
        <p className="text-[10px] uppercase tracking-wide text-white/45">Последние jobs</p>
        {!recent.length ? (
          <p className="mt-2 text-xs text-genesis-muted">
            Пока пусто — job появится после оплаты Stripe (Landing).
          </p>
        ) : (
          <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-xs">
            {recent.map((j, i) => (
              <li
                key={`${j.job_id}-${i}`}
                className="flex justify-between gap-2 rounded border border-white/5 bg-black/20 px-2 py-1.5"
              >
                <span className="truncate text-white/85">
                  {j.work_type} · {j.order_id} · {j.status}
                </span>
                <span className="shrink-0 tabular-nums text-genesis-muted">
                  {String(j.at || "").slice(11, 19) || "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
