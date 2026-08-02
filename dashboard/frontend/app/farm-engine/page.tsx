"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { FarmMaturityBoard, type FarmMaturity } from "../components/FarmMaturityBoard";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Opp = {
  id: string;
  title?: string;
  description_ru?: string;
  kind?: string;
  pipeline_stage?: string;
  ceo_decision?: string;
  can_enqueue?: boolean;
  legal?: { ok?: boolean; decision?: string; notes_ru?: string; blockers?: string[] };
  roi?: {
    ok?: boolean;
    est_profit_eur?: number;
    est_margin_pct?: number;
    reason_ru?: string;
  };
};

type EarnPlatform = {
  id: string;
  title?: string;
  track?: string;
  first_payout_score?: number;
  autonomy_score?: number;
  opinion_ru?: string;
  pipeline_stage?: string;
  is_first_pick?: boolean;
  earn_fit?: { ok?: boolean; missing?: string[] };
};

type Panel = {
  ok?: boolean;
  pipeline_ru?: string[];
  forbidden_ru?: string[];
  maturity?: FarmMaturity;
  strategy?: {
    architecture_ready_ru?: string;
    strategic_question_ru?: string;
    first_live_earn_choice_ru?: string;
    north_star_ru?: string;
    tracks?: { id: string; title_ru: string; goal_ru: string; focus_ru?: string }[];
    do_not_ru?: string[];
  };
  earn_platforms?: {
    title_ru?: string;
    law_ru?: string;
    platforms?: EarnPlatform[];
    counts?: Record<string, number>;
  };
  scan?: {
    law_ru?: string;
    mode?: string;
    counts?: Record<string, number>;
    opportunities?: Opp[];
  };
  queue?: { jobs?: { job_id?: string; title?: string; status?: string; at?: string }[]; note_ru?: string };
  ledger?: {
    confirmed_eur?: number;
    pending_eur?: number;
    formula_ru?: string;
    note_ru?: string;
  };
};

export default function FarmEnginePage() {
  const [data, setData] = useState<Panel | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/engine/v1`);
      if (!res.ok) throw new Error("farm_engine");
      setData(await res.json());
      setError("");
    } catch {
      setError("Backend недоступен — запустите Genesis.exe");
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 20_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  async function decide(id: string, decision: string) {
    setBusy(`${id}:${decision}`);
    try {
      const q = new URLSearchParams({ opportunity_id: id, decision });
      const res = await fetch(`${API}/api/farm/engine/v1/decide?${q}`, { method: "POST" });
      const body = await res.json();
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "decide failed"));
      } else {
        setData(body.scan ? { ...data, scan: body.scan } : data);
        await refresh();
      }
    } catch {
      setError("decide failed");
    } finally {
      setBusy("");
    }
  }

  async function enqueue(id: string) {
    setBusy(`${id}:enqueue`);
    try {
      const q = new URLSearchParams({ opportunity_id: id });
      const res = await fetch(`${API}/api/farm/engine/v1/enqueue?${q}`, { method: "POST" });
      const body = await res.json();
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "enqueue failed"));
      }
      await refresh();
    } catch {
      setError("enqueue failed");
    } finally {
      setBusy("");
    }
  }

  const opps = data?.scan?.opportunities || [];
  const counts = data?.scan?.counts || {};

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <header className="text-center">
        <p className="text-xs uppercase tracking-widest text-genesis-muted">
          Farm Engine v1 · отдельно от Path A
        </p>
        <h1 className="mt-2 text-2xl font-bold text-white">Легальная цифровая работа</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          A: первый Confirmed € (API+Stripe) · B: искать новые Earn-платформы. Без капч и
          performer-ботов.
        </p>
        <div className="mt-3 flex flex-wrap justify-center gap-2 text-xs">
          <Link href="/" className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5">
            Ферма разметки
          </Link>
          <Link
            href="/payout"
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5"
          >
            Вывод
          </Link>
          <Link
            href="/acquisition"
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5"
          >
            Path A Desk
          </Link>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </p>
      ) : null}

      {data?.maturity ? <FarmMaturityBoard data={data.maturity} /> : null}

      {data?.strategy ? (
        <section className="rounded-xl border border-emerald-500/25 bg-emerald-950/15 p-4 text-sm space-y-3">
          <p className="text-xs text-genesis-muted">{data.strategy.architecture_ready_ru}</p>
          <p className="font-medium text-emerald-50">
            {data.strategy.strategic_question_ru}
          </p>
          <p className="text-[11px] text-white/80">
            Выбор сейчас: {data.strategy.first_live_earn_choice_ru}
          </p>
          <div className="grid gap-2 md:grid-cols-2">
            {(data.strategy.tracks || []).map((t) => (
              <div
                key={t.id}
                className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs"
              >
                <p className="font-medium text-white/90">{t.title_ru}</p>
                <p className="mt-1 text-genesis-muted">{t.goal_ru}</p>
                {t.focus_ru ? (
                  <p className="mt-1 text-emerald-100/80">{t.focus_ru}</p>
                ) : null}
              </div>
            ))}
          </div>
          <p className="text-[11px] text-white/75">{data.strategy.north_star_ru}</p>
          {(data.strategy.do_not_ru || []).length ? (
            <ul className="list-inside list-disc text-[11px] text-rose-200/80">
              {data.strategy.do_not_ru!.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {data?.earn_platforms ? (
        <section className="rounded-xl border border-sky-500/25 bg-sky-950/15 p-4 text-sm space-y-2">
          <h2 className="text-sm font-semibold text-sky-50">
            {data.earn_platforms.title_ru ?? "Earn Platform Scanner (B)"}
          </h2>
          <p className="text-[11px] text-genesis-muted">{data.earn_platforms.law_ru}</p>
          <ul className="space-y-2">
            {(data.earn_platforms.platforms || []).map((p) => (
              <li
                key={p.id}
                className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium text-white/90">
                    {p.is_first_pick ? "★ " : ""}
                    {p.title}
                  </span>
                  <span className="text-genesis-muted">
                    track {p.track} · {p.pipeline_stage} · payout {p.first_payout_score}/5 ·
                    autonomy {p.autonomy_score}/5
                  </span>
                </div>
                <p className="mt-1 text-genesis-muted">{p.opinion_ru}</p>
                <p className="mt-0.5 text-[10px] text-white/60">
                  Earn fit: {p.earn_fit?.ok ? "4/4 PASS" : `missing ${(p.earn_fit?.missing || []).join(", ") || "—"}`}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
        <p className="text-xs text-genesis-muted">{data?.scan?.law_ru}</p>
        <p className="mt-2 text-white/90">
          Режим: {data?.scan?.mode || "—"} · Legal pass {counts.legal_pass ?? 0} · ROI pass{" "}
          {counts.roi_pass ?? 0} · Ready to enqueue {counts.execution_ready ?? 0} · Rejected{" "}
          {counts.legal_reject ?? 0}
        </p>
        <p className="mt-2 text-xs text-genesis-muted">
          Pipeline: {(data?.pipeline_ru || []).join(" → ")}
        </p>
        <ul className="mt-2 list-inside list-disc text-xs text-rose-200/80">
          {(data?.forbidden_ru || []).map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-white">Opportunity Scanner</h2>
        {opps.map((o) => (
          <article
            key={o.id}
            className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-medium text-white">{o.title}</h3>
              <span className="text-[11px] text-genesis-muted">{o.pipeline_stage}</span>
            </div>
            <p className="mt-1 text-xs text-genesis-muted">{o.description_ru}</p>
            <p className="mt-2 text-xs">
              Legal: {o.legal?.ok ? "PASS" : "REJECT"} · ROI:{" "}
              {o.roi?.ok
                ? `PASS · ~${o.roi.est_profit_eur} €/job (${o.roi.est_margin_pct}%)`
                : "REJECT"}{" "}
              · CEO: {o.ceo_decision}
            </p>
            {o.legal?.notes_ru ? (
              <p className="mt-1 text-[11px] text-white/60">{o.legal.notes_ru}</p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              {(["research", "hold", "go", "reject"] as const).map((d) => (
                <button
                  key={d}
                  type="button"
                  disabled={!!busy}
                  onClick={() => void decide(o.id, d)}
                  className="rounded-lg border border-white/15 px-2.5 py-1 hover:bg-white/5 disabled:opacity-40"
                >
                  {d}
                </button>
              ))}
              {o.can_enqueue ? (
                <button
                  type="button"
                  disabled={!!busy}
                  onClick={() => void enqueue(o.id)}
                  className="rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-2.5 py-1 text-emerald-100 hover:bg-emerald-950/50 disabled:opacity-40"
                >
                  Enqueue dry_run
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
        <h2 className="text-sm font-semibold text-white">Execution Queue</h2>
        <p className="mt-1 text-xs text-genesis-muted">{data?.queue?.note_ru}</p>
        <ul className="mt-2 space-y-1 text-xs text-white/80">
          {(data?.queue?.jobs || []).slice(0, 8).map((j) => (
            <li key={j.job_id}>
              {String(j.at || "").slice(11, 19)} · {j.status} · {j.title}
            </li>
          ))}
          {!data?.queue?.jobs?.length ? <li className="text-genesis-muted">Пусто</li> : null}
        </ul>
      </section>

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
        <h2 className="text-sm font-semibold text-white">Profit Ledger</h2>
        <p className="mt-1 text-white/90">
          Confirmed {data?.ledger?.confirmed_eur ?? 0} € · Pending {data?.ledger?.pending_eur ?? 0} €
        </p>
        <p className="mt-1 text-xs text-genesis-muted">{data?.ledger?.formula_ru}</p>
        <p className="mt-1 text-xs text-genesis-muted">{data?.ledger?.note_ru}</p>
      </section>
    </main>
  );
}
