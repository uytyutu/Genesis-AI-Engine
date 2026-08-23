"use client";

import { useCallback, useEffect, useState } from "react";
import { getBackendApiBase } from "../lib/backendApiBase";

const API = getBackendApiBase();

type FailedJob = {
  task_id?: string;
  title?: string;
  stage?: string;
  error?: string;
  retry_count?: number;
  next_retry?: string | null;
  blocker?: string;
};

type QueuesPayload = {
  separation_ru?: string;
  bounty?: {
    pending?: number;
    running?: number;
    failed?: number;
    completed?: number;
    pending_execution?: FailedJob[];
    failed_jobs?: FailedJob[];
    watchdog?: { alive?: boolean; max_execution_attempts?: number };
    worker?: string;
    policy?: { advance_on_fail?: boolean; note_ru?: string };
  };
  api_farm?: {
    candidates?: number;
    building?: number;
    testing?: number;
    ready?: number;
    published?: number;
    active?: number;
    revenue?: { actual?: number; pending?: number; gross?: number };
    worker?: string;
    ceo_action?: string[];
  };
  revenue_farm?: {
    actual_revenue?: number;
    pending_payout?: number;
    paypal_payout_confirmed?: boolean;
    rule_ru?: string;
  };
};

export function FarmQueuesPanel({ compact }: { compact?: boolean }) {
  const [data, setData] = useState<QueuesPayload | null>(null);
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/queues`);
      const json = await res.json();
      setData(json);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "queues load failed");
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  const b = data?.bounty;
  const a = data?.api_farm;
  const r = data?.revenue_farm;

  return (
    <section className="rounded-2xl border border-sky-500/30 bg-sky-950/15 p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-sky-100">Farm Queues</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            {data?.separation_ru ?? "Bounty ≠ API Farm ≠ Revenue"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded-lg border border-white/15 px-2 py-1 text-xs text-genesis-muted"
        >
          Refresh
        </button>
      </div>
      {err ? <p className="mt-2 text-xs text-amber-200">{err}</p> : null}

      <div className={`mt-4 grid gap-3 ${compact ? "grid-cols-1" : "md:grid-cols-2"}`}>
        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
          <p className="text-sm font-medium text-white">BOUNTIES</p>
          <p className="mt-1 text-[10px] text-genesis-muted">{b?.worker}</p>
          <div className="mt-2 grid grid-cols-4 gap-1 text-center text-xs">
            {[
              ["Pending", b?.pending],
              ["Running", b?.running],
              ["Failed", b?.failed],
              ["Done", b?.completed],
            ].map(([l, v]) => (
              <div key={String(l)} className="rounded border border-white/10 px-1 py-1">
                <p className="text-[10px] text-genesis-muted">{l}</p>
                <p className="font-semibold tabular-nums">{Number(v ?? 0)}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-genesis-muted">
            Watchdog: {b?.watchdog?.alive ? "alive" : "off"} · advance_on_fail=
            {String(b?.policy?.advance_on_fail ?? false)}
          </p>
          {(b?.failed_jobs || []).slice(0, compact ? 2 : 4).map((j) => (
            <div
              key={j.task_id}
              className="mt-2 rounded border border-rose-500/30 bg-rose-950/20 px-2 py-1.5 text-[11px] text-rose-100"
            >
              <p className="font-medium">{j.title || j.task_id}</p>
              <p className="text-rose-100/80">
                stage={j.stage} · retry={j.retry_count} · next={j.next_retry || "—"}
              </p>
              <p className="mt-0.5 break-words">{j.error}</p>
              <p className="text-amber-100/90">blocker: {j.blocker}</p>
            </div>
          ))}
          {(b?.pending_execution || []).slice(0, compact ? 2 : 3).map((j) => (
            <div
              key={`p-${j.task_id}`}
              className="mt-2 rounded border border-amber-500/30 bg-amber-950/20 px-2 py-1.5 text-[11px] text-amber-100"
            >
              <p className="font-medium">pending_execution · {j.title || j.task_id}</p>
              <p>
                stage={j.stage} · retry={j.retry_count} · next={j.next_retry || "soon"}
              </p>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3">
          <p className="text-sm font-medium text-violet-100">API FARM</p>
          <p className="mt-1 text-[10px] text-genesis-muted">{a?.worker}</p>
          <div className="mt-2 grid grid-cols-3 gap-1 text-center text-xs sm:grid-cols-6">
            {[
              ["Cand", a?.candidates],
              ["Build", a?.building],
              ["Test", a?.testing],
              ["Ready", a?.ready],
              ["Pub", a?.published],
              ["Active", a?.active],
            ].map(([l, v]) => (
              <div key={String(l)} className="rounded border border-white/10 px-1 py-1">
                <p className="text-[10px] text-genesis-muted">{l}</p>
                <p className="font-semibold tabular-nums">{Number(v ?? 0)}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-emerald-200/90">
            Revenue Actual {Number(a?.revenue?.actual ?? r?.actual_revenue ?? 0).toFixed(2)} ·
            Pending {Number(a?.revenue?.pending ?? r?.pending_payout ?? 0).toFixed(2)} · PayPal{" "}
            {r?.paypal_payout_confirmed ? "flag on" : "CEO ACTION"}
          </p>
          {(a?.ceo_action || []).slice(0, 3).map((line) => (
            <p key={line} className="mt-1 text-[11px] text-amber-100/90">
              · {line}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}
