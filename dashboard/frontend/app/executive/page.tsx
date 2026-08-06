"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Milestone = { id: string; label: string; done: boolean };
type FocusItem = {
  id: string;
  track?: string;
  label?: string;
  label_ru?: string;
  href?: string;
  priority?: number;
  done?: boolean;
};

type CeoDash = {
  ok?: boolean;
  title?: string;
  subtitle?: string;
  kpi_law_ru?: string;
  tracks?: { virtus?: string; farm?: string };
  virtus?: {
    first_clients?: { count?: number; goal?: number; remaining?: number; pct?: number };
    revenue_eur?: number;
    mrr_eur?: number;
    websites_sold?: number;
    ai_stores_sold?: number;
    repeat_clients?: number;
    milestones?: Milestone[];
    finish_line_ru?: string;
  };
  farm?: {
    scanned?: number;
    high_roi?: number;
    approved?: number;
    executed?: number;
    draft_pr?: number;
    merged?: number;
    confirmed_usd?: number;
    payout_usd?: number;
    paid_count?: number;
    win_rate?: number | null;
    avg_hours?: number | null;
    avg_earn_usd?: number | null;
    bottleneck_ru?: string;
    next_unlock_ru?: string;
    avg_execution_s?: number | null;
    execution_success?: {
      approved?: number;
      started?: number;
      completed?: number;
      failed?: number;
      skipped?: number;
      start_rate?: number | null;
      complete_rate?: number | null;
      avg_execution_s?: number | null;
    };
  };
  first_real_euro?: {
    reached?: boolean;
    status?: string;
    mark?: string;
    detail_ru?: string;
    note_ru?: string;
    ledger_confirmed_eur?: number;
    opire_confirmed_usd?: number;
  };
  growth_ladder?: {
    title?: string;
    title_ru?: string;
    note_ru?: string;
    current?: { id?: string; label?: string; reached?: boolean; progress?: string };
    steps?: Array<{ id: string; label: string; reached?: boolean; progress?: string }>;
  };
  weekly_constraint?: {
    label?: string;
    phase?: string;
    question_ru?: string;
    id?: string;
    constraint?: string;
    metric?: string;
    owner?: string;
    impact?: string;
    action?: string;
    answer_ru?: string;
    href?: string;
    rule_ru?: string;
  };
  phase?: {
    id?: string;
    name?: string;
    name_ru?: string;
    goal_ru?: string;
    mode?: string;
    rule_ru?: string;
    frozen_ru?: string;
    kpis?: string[];
  };
  income_contours?: {
    title_ru?: string;
    sink_ru?: string;
    farms?: { id: string; label: string; role_ru?: string; href?: string }[];
  };
  frontend_deployment?: {
    title?: string;
    local_commit?: string;
    production_commit?: string | null;
    production_url?: string;
    status?: string;
    mark?: string;
    deploy?: string;
    behind?: boolean | null;
    detail_ru?: string;
    note_ru?: string;
    checklist_ru?: string[];
    local_dirty?: boolean;
  };
  dashboard_health?: {
    title?: string;
    headline_ru?: string;
    summary?: { green?: number; yellow?: number; red?: number };
    items?: Array<{
      id: string;
      label: string;
      status: string;
      mark?: string;
      detail_ru?: string;
      href?: string;
    }>;
  };
  company?: {
    launch_readiness_pct?: number;
    performance_pct?: number;
    documentation_pct?: number;
    golden_website_pct?: number;
    website_launch?: string;
    ads_allowed?: boolean;
    focus?: string;
    factory_metrics?: {
      ok?: boolean;
      title?: string;
      count?: number;
      avg_total_e2e_s?: number | null;
      avg_zip_pack_s?: number | null;
      p50_total_e2e_s?: number | null;
      cached_zip_hits?: number;
      targets_s?: { stage1?: number; stage2?: number; stage3?: number };
      stage_table?: Array<{
        id?: string;
        label?: string;
        avg_s?: number | null;
        p50_s?: number | null;
        samples?: number;
        status?: string;
      }>;
    };
    demo_gallery?: {
      status?: string;
      preview?: string;
      visual_quality?: number;
      visual_quality_gate?: {
        status?: string;
        ok?: boolean;
        pass?: number;
        goal?: number;
        ssot?: string;
      };
      last_generated?: string | null;
      websites?: { pass?: number; goal?: number };
      stores?: { pass?: number; goal?: number };
    };
    golden_website_test?: {
      status?: string;
      functional_status?: string;
      logic_status?: string;
      infrastructure_status?: string;
      performance_status?: string;
      layers?: {
        functional?: { status?: string; label?: string; detail?: string };
        logic?: { status?: string; label?: string; detail?: string };
        infrastructure?: { status?: string; label?: string; detail?: string };
        performance?: { status?: string; label?: string; detail?: string };
      };
      website_launch?: string;
      ads_allowed?: boolean;
      focus?: string;
      reasons?: string[];
      blockers?: Array<{
        id: string;
        label: string;
        status: string;
        detail?: string;
      }>;
      launch_blockers?: Array<{
        id: string;
        label: string;
        status: string;
        detail?: string;
      }>;
      live_prices_de?: { basic?: number; business?: number; premium?: number };
    };
  };
  today_focus?: FocusItem[];
};

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-white/5 py-1.5 text-sm last:border-0">
      <span className="text-zinc-400">{label}</span>
      <span className="font-semibold tabular-nums text-white">{value}</span>
    </div>
  );
}

export default function ExecutiveDashboardPage() {
  const [data, setData] = useState<CeoDash | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(`${API}/api/owner/ceo-dashboard`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData((await res.json()) as CeoDash);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "load_failed");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const v = data?.virtus;
  const f = data?.farm;
  const c = data?.company;
  const clients = v?.first_clients;

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8 text-zinc-100">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-zinc-500">
            {BRAND_NAME} · Mission Control
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-white">
            {data?.title || "CEO Dashboard"}
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            {data?.subtitle || "Чем заниматься сегодня"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/global-analytics"
            className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
          >
            Global Analytics
          </Link>
          <button
            type="button"
            disabled={busy}
            onClick={() => void load()}
            className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
          >
            Обновить
          </button>
        </div>
      </header>

      {err ? <p className="text-sm text-rose-200">{err}</p> : null}

      {data?.phase ? (
        <section className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-zinc-500">
            Phase {data.phase.id} · {data.phase.name}
          </p>
          <p className="mt-1 text-sm text-zinc-200">{data.phase.goal_ru}</p>
          <p className="mt-1 text-[11px] text-zinc-500">
            {data.phase.rule_ru} · {data.phase.frozen_ru}
          </p>
        </section>
      ) : null}

      {data?.income_contours ? (
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <h2 className="text-sm font-semibold text-white">
            {data.income_contours.title_ru || "Три контура дохода"}
          </h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {(data.income_contours.farms || []).map((f) => (
              <Link
                key={f.id}
                href={f.href || "/executive"}
                className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs hover:bg-white/5"
              >
                <p className="font-semibold text-white">{f.label}</p>
                <p className="mt-1 text-[10px] text-zinc-400">{f.role_ru}</p>
              </Link>
            ))}
          </div>
          {data.income_contours.sink_ru ? (
            <p className="mt-2 text-[11px] text-zinc-500">{data.income_contours.sink_ru}</p>
          ) : null}
        </section>
      ) : null}

      {data?.frontend_deployment ? (
        <section
          className={`rounded-xl border p-4 ${
            data.frontend_deployment.status === "in_sync"
              ? "border-emerald-500/35 bg-emerald-950/20"
              : data.frontend_deployment.status === "behind"
                ? "border-rose-500/35 bg-rose-950/20"
                : "border-amber-500/30 bg-amber-950/15"
          }`}
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">
              {data.frontend_deployment.title || "Frontend Deployment"}
            </h2>
            <span className="text-sm">
              {data.frontend_deployment.mark}{" "}
              {data.frontend_deployment.status === "behind"
                ? "Production is behind local"
                : data.frontend_deployment.status === "in_sync"
                  ? "In sync"
                  : data.frontend_deployment.status || "unknown"}
            </span>
          </div>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[10px] uppercase text-zinc-500">Local commit</dt>
              <dd className="font-mono text-white">
                {data.frontend_deployment.local_commit || "—"}
                {data.frontend_deployment.local_dirty ? " · dirty" : ""}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase text-zinc-500">Production commit</dt>
              <dd className="font-mono text-white">
                {data.frontend_deployment.production_commit || "unknown"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase text-zinc-500">Deploy</dt>
              <dd className="font-semibold text-amber-100">
                {data.frontend_deployment.deploy || "UNKNOWN"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase text-zinc-500">Production URL</dt>
              <dd className="truncate text-sky-200">
                {data.frontend_deployment.production_url || "—"}
              </dd>
            </div>
          </dl>
          <p className="mt-2 text-xs text-zinc-300">{data.frontend_deployment.detail_ru}</p>
          {data.frontend_deployment.note_ru ? (
            <p className="mt-1 text-[11px] text-zinc-500">{data.frontend_deployment.note_ru}</p>
          ) : null}
          {data.frontend_deployment.checklist_ru?.length ? (
            <ul className="mt-2 space-y-0.5 text-[10px] text-zinc-500">
              {data.frontend_deployment.checklist_ru.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {data?.first_real_euro ? (
        <section
          className={`rounded-xl border p-4 ${
            data.first_real_euro.reached
              ? "border-emerald-500/35 bg-emerald-950/20"
              : "border-zinc-500/30 bg-zinc-900/40"
          }`}
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">First Real Euro</h2>
            <span className="text-lg">
              {data.first_real_euro.mark}{" "}
              {data.first_real_euro.reached ? "reached" : "not reached"}
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-300">{data.first_real_euro.detail_ru}</p>
          {data.first_real_euro.note_ru ? (
            <p className="mt-1 text-[11px] text-zinc-500">{data.first_real_euro.note_ru}</p>
          ) : null}
          {data.growth_ladder?.steps?.length ? (
            <ol className="mt-3 flex flex-wrap gap-2 text-[10px]">
              {data.growth_ladder.steps.map((s) => (
                <li
                  key={s.id}
                  className={`rounded-full border px-2.5 py-1 ${
                    s.reached
                      ? "border-emerald-400/40 bg-emerald-950/30 text-emerald-100"
                      : s.id === data.growth_ladder?.current?.id
                        ? "border-amber-400/40 bg-amber-950/25 text-amber-100"
                        : "border-white/10 text-zinc-500"
                  }`}
                  title={s.progress || s.label}
                >
                  {s.reached ? "✓" : "○"} {s.label}
                </li>
              ))}
            </ol>
          ) : null}
        </section>
      ) : null}

      {data?.weekly_constraint ? (
        <section className="rounded-xl border border-amber-500/35 bg-amber-950/20 p-4">
          <p className="text-[10px] uppercase tracking-wide text-amber-200/80">
            {data.weekly_constraint.label || "THIS WEEK"}
          </p>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
              <dt className="w-20 shrink-0 text-[11px] uppercase text-zinc-500">Constraint</dt>
              <dd className="font-semibold text-white">
                {data.weekly_constraint.constraint || data.weekly_constraint.metric}
              </dd>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
              <dt className="w-20 shrink-0 text-[11px] uppercase text-zinc-500">Owner</dt>
              <dd className="text-zinc-200">{data.weekly_constraint.owner || "CEO"}</dd>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
              <dt className="w-20 shrink-0 text-[11px] uppercase text-zinc-500">Impact</dt>
              <dd className="text-zinc-300">
                {data.weekly_constraint.impact || data.weekly_constraint.answer_ru}
              </dd>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
              <dt className="w-20 shrink-0 text-[11px] uppercase text-zinc-500">Action</dt>
              <dd className="text-amber-100">{data.weekly_constraint.action}</dd>
            </div>
          </dl>
          {data.weekly_constraint.rule_ru ? (
            <p className="mt-3 text-[11px] text-zinc-500">{data.weekly_constraint.rule_ru}</p>
          ) : null}
          {data.weekly_constraint.href ? (
            <Link
              href={data.weekly_constraint.href}
              className="mt-3 inline-block text-xs text-amber-200 underline hover:text-white"
            >
              Открыть узкое место →
            </Link>
          ) : null}
        </section>
      ) : null}

      {data?.dashboard_health ? (
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">
              {data.dashboard_health.title || "CEO Dashboard Health"}
            </h2>
            <span className="text-[11px] text-zinc-500">
              {data.dashboard_health.headline_ru}
            </span>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
            {(data.dashboard_health.items || []).map((h) => (
              <Link
                key={h.id}
                href={h.href || "/executive"}
                className="rounded-lg border border-white/10 bg-black/25 px-2.5 py-2 hover:bg-white/5"
              >
                <p className="text-sm">
                  {h.mark} <span className="font-medium text-white">{h.label}</span>
                </p>
                <p className="mt-1 text-[10px] leading-snug text-zinc-400">{h.detail_ru}</p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="rounded-xl border border-emerald-500/25 bg-emerald-950/15 p-4">
        <h2 className="text-sm font-semibold text-emerald-100">Today Focus</h2>
        <ul className="mt-3 space-y-2">
          {(data?.today_focus || []).map((item) => (
            <li key={item.id}>
              <Link
                href={item.href || "/"}
                className="flex items-start gap-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm hover:bg-white/5"
              >
                <span className={item.done ? "text-emerald-300" : "text-zinc-500"}>
                  {item.done ? "☑" : "☐"}
                </span>
                <span>
                  <span className="text-white">{item.label_ru || item.label}</span>
                  <span className="mt-0.5 block text-[10px] uppercase tracking-wide text-zinc-500">
                    {item.track}
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-sky-500/20 bg-sky-950/10 p-4">
          <h2 className="text-sm font-semibold text-sky-100">Virtus Core</h2>
          <p className="mt-1 text-[11px] text-zinc-500">{data?.tracks?.virtus}</p>
          <div className="mt-3">
            <Row
              label="First Client"
              value={`${clients?.count ?? 0} / ${clients?.goal ?? 5}`}
            />
            <Row label="Revenue" value={`${Number(v?.revenue_eur || 0).toFixed(0)} €`} />
            <Row label="MRR" value={`${Number(v?.mrr_eur || 0).toFixed(0)} €`} />
            <Row label="Websites" value={v?.websites_sold ?? 0} />
            <Row label="AI Store" value={v?.ai_stores_sold ?? 0} />
            <Row label="Repeat Clients" value={v?.repeat_clients ?? 0} />
          </div>
          <ul className="mt-3 space-y-1 text-[11px] text-zinc-400">
            {(v?.milestones || []).map((m) => (
              <li key={m.id}>
                <span className={m.done ? "text-emerald-300" : "text-zinc-600"}>
                  {m.done ? "●" : "○"}
                </span>{" "}
                {m.label}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-4">
          <h2 className="text-sm font-semibold text-amber-100">Farm Engine</h2>
          <p className="mt-1 text-[11px] text-zinc-500">{data?.tracks?.farm}</p>
          <div className="mt-3">
            <Row label="Scanned" value={f?.scanned ?? 0} />
            <Row label="High ROI" value={f?.high_roi ?? 0} />
            <Row label="Approved" value={f?.approved ?? 0} />
            <Row label="Executed" value={f?.executed ?? 0} />
            <Row label="Draft PR" value={f?.draft_pr ?? 0} />
            <Row label="Merged" value={f?.merged ?? 0} />
            <Row
              label="Avg Execution"
              value={
                f?.avg_execution_s != null || f?.execution_success?.avg_execution_s != null
                  ? `${f?.avg_execution_s ?? f?.execution_success?.avg_execution_s}s`
                  : "—"
              }
            />
            <Row
              label="Start / Complete"
              value={
                f?.execution_success?.start_rate != null
                  ? `${Math.round((f.execution_success.start_rate || 0) * 100)}% / ${
                      f.execution_success.complete_rate != null
                        ? `${Math.round(f.execution_success.complete_rate * 100)}%`
                        : "—"
                    }`
                  : "—"
              }
            />
            <Row
              label="Confirmed"
              value={`${Number(f?.confirmed_usd || 0).toFixed(0)} $`}
            />
            <Row label="Payout" value={`${Number(f?.payout_usd || 0).toFixed(0)} $`} />
          </div>
          {(f?.win_rate != null || f?.avg_hours != null) && (
            <p className="mt-2 text-[11px] text-zinc-500">
              {f.win_rate != null ? `Win rate ${f.win_rate}%` : ""}
              {f.avg_hours != null ? ` · avg ${f.avg_hours}h` : ""}
              {f.avg_earn_usd != null ? ` · $${f.avg_earn_usd}/task` : ""}
            </p>
          )}
          {f?.bottleneck_ru ? (
            <p className="mt-2 text-[11px] text-amber-100/80">{f.bottleneck_ru}</p>
          ) : null}
        </section>
      </div>

      <section className="rounded-xl border border-sky-500/25 bg-sky-950/15 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-sm font-semibold text-white">Factory Metrics</h2>
          <span className="text-xs text-zinc-500">
            {c?.factory_metrics?.count ?? 0} builds · targets{" "}
            {c?.factory_metrics?.targets_s?.stage1 ?? 180}/
            {c?.factory_metrics?.targets_s?.stage2 ?? 120}/
            {c?.factory_metrics?.targets_s?.stage3 ?? 90}s
          </span>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Avg E2E</p>
            <p className="text-lg font-semibold text-white">
              {c?.factory_metrics?.avg_total_e2e_s != null
                ? `${c.factory_metrics.avg_total_e2e_s}s`
                : "—"}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Avg ZIP pack</p>
            <p className="text-lg font-semibold text-white">
              {c?.factory_metrics?.avg_zip_pack_s != null
                ? `${c.factory_metrics.avg_zip_pack_s}s`
                : "—"}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">ZIP cache hits</p>
            <p className="text-lg font-semibold text-white">
              {c?.factory_metrics?.cached_zip_hits ?? 0}
            </p>
          </div>
        </div>
        {(c?.factory_metrics?.stage_table || []).length > 0 ? (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[280px] text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-zinc-500">
                  <th className="py-1.5 pr-3 font-medium">Stage</th>
                  <th className="py-1.5 pr-3 font-medium text-right">Avg</th>
                  <th className="py-1.5 pr-3 font-medium text-right">p50</th>
                  <th className="py-1.5 font-medium text-right">n</th>
                </tr>
              </thead>
              <tbody>
                {(c?.factory_metrics?.stage_table || []).map(
                  (row: {
                    id?: string;
                    label?: string;
                    avg_s?: number | null;
                    p50_s?: number | null;
                    samples?: number;
                  }) => (
                    <tr key={row.id || row.label} className="border-b border-white/5">
                      <td className="py-1.5 pr-3 text-zinc-300">{row.label || row.id}</td>
                      <td className="py-1.5 pr-3 text-right font-medium text-white">
                        {row.avg_s != null ? `${row.avg_s}s` : "—"}
                      </td>
                      <td className="py-1.5 pr-3 text-right text-zinc-400">
                        {row.p50_s != null ? `${row.p50_s}s` : "—"}
                      </td>
                      <td className="py-1.5 text-right text-zinc-500">{row.samples ?? 0}</td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        ) : null}
        <p className="mt-2 text-[11px] text-zinc-500">
          Trace: Queue → Template → Content → Assets → Render → Gates → ZIP. Ladder:
          &lt;180s → &lt;120s → &lt;90s. After Ready, ZIP is immutable (cache only).
        </p>
      </section>

      <section className="rounded-xl border border-sky-500/25 bg-sky-950/15 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-sm font-semibold text-white">Demo Gallery</h2>
          <span
            className={`text-xs font-semibold uppercase tracking-wide ${
              c?.demo_gallery?.status === "PASS" ? "text-emerald-300" : "text-amber-200"
            }`}
          >
            {c?.demo_gallery?.status ?? "—"}
          </span>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Website</p>
            <p className="text-lg font-semibold text-white">
              {c?.demo_gallery?.websites?.pass ?? 0} / {c?.demo_gallery?.websites?.goal ?? 8}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">AI Store</p>
            <p className="text-lg font-semibold text-white">
              {c?.demo_gallery?.stores?.pass ?? 0} / {c?.demo_gallery?.stores?.goal ?? 6}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Preview</p>
            <p className="text-lg font-semibold text-white">{c?.demo_gallery?.preview ?? "—"}</p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">VQ Gate</p>
            <p
              className={`text-lg font-semibold ${
                c?.demo_gallery?.visual_quality_gate?.status === "PASS"
                  ? "text-emerald-300"
                  : "text-amber-200"
              }`}
            >
              {c?.demo_gallery?.visual_quality_gate?.status ?? "—"}
              {typeof c?.demo_gallery?.visual_quality_gate?.pass === "number"
                ? ` ${c.demo_gallery.visual_quality_gate.pass}/${c.demo_gallery.visual_quality_gate.goal ?? 8}`
                : ""}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Bytes score</p>
            <p className="text-lg font-semibold text-white">
              {c?.demo_gallery?.visual_quality ?? 0} / 100
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2 sm:col-span-2 lg:col-span-1">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">Last Generated</p>
            <p className="text-sm font-semibold text-white">
              {c?.demo_gallery?.last_generated
                ? new Date(c.demo_gallery.last_generated).toLocaleString("de-DE")
                : "—"}
            </p>
          </div>
        </div>
        <p className="mt-2 text-[11px] text-zinc-500">
          Gallery PASS = full demos (≥5 KB). Visual Quality Gate = no empty Hero slots on Business — separate
          launch blocker.
        </p>
      </section>

      <section className="rounded-xl border border-rose-500/25 bg-rose-950/15 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-sm font-semibold text-white">Public Launch Blockers</h2>
          <span
            className={`text-xs font-semibold uppercase tracking-wide ${
              c?.website_launch === "READY" ? "text-emerald-300" : "text-rose-300"
            }`}
          >
            Website Launch {c?.website_launch ?? "BLOCKED"}
          </span>
        </div>
        <p className="mt-1 text-[11px] text-zinc-500">
          {c?.focus || "Ads blocked until Golden Website Test PASS"}
        </p>
        {(c?.golden_website_test?.functional_status ||
          c?.golden_website_test?.logic_status ||
          c?.golden_website_test?.infrastructure_status ||
          c?.golden_website_test?.performance_status) && (
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <div className="rounded-lg border border-emerald-500/25 bg-emerald-950/20 px-3 py-2">
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Functional · {c?.golden_website_test?.functional_status ?? c?.golden_website_test?.logic_status ?? "—"}
              </p>
              <p className="mt-1 text-xs text-zinc-300">
                {c?.golden_website_test?.layers?.functional?.detail ||
                  c?.golden_website_test?.layers?.logic?.detail ||
                  "Commercial pipeline"}
              </p>
            </div>
            <div
              className={`rounded-lg border px-3 py-2 ${
                String(c?.golden_website_test?.infrastructure_status || "").startsWith("PASS")
                  ? "border-emerald-500/25 bg-emerald-950/20"
                  : "border-amber-500/30 bg-amber-950/20"
              }`}
            >
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Infrastructure · {c?.golden_website_test?.infrastructure_status ?? "—"}
              </p>
              <p className="mt-1 text-xs text-zinc-300">
                {c?.golden_website_test?.layers?.infrastructure?.detail ||
                  "HTTP ZIP + uvicorn port"}
              </p>
            </div>
            <div
              className={`rounded-lg border px-3 py-2 ${
                c?.golden_website_test?.performance_status === "PASS"
                  ? "border-emerald-500/25 bg-emerald-950/20"
                  : "border-amber-500/30 bg-amber-950/20"
              }`}
            >
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Performance · {c?.golden_website_test?.performance_status ?? "—"}
              </p>
              <p className="mt-1 text-xs text-zinc-300">
                {c?.golden_website_test?.layers?.performance?.detail ||
                  "ZIP/Factory time KPIs"}
              </p>
            </div>
          </div>
        )}
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {(c?.golden_website_test?.launch_blockers || c?.golden_website_test?.blockers || []).map(
            (b) => (
              <div
                key={b.id}
                className={`rounded-lg border px-3 py-2 ${
                  b.status === "done"
                    ? "border-emerald-500/25 bg-emerald-950/20"
                    : "border-rose-500/30 bg-rose-950/20"
                }`}
              >
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                  {b.status === "done" ? "PASS" : "BLOCKER"} · {b.label}
                </p>
                <p className="mt-1 text-xs text-zinc-300">{b.detail}</p>
              </div>
            ),
          )}
        </div>
        {c?.golden_website_test?.live_prices_de ? (
          <p className="mt-3 text-[11px] text-zinc-500">
            Live DE prices: {c.golden_website_test.live_prices_de.basic}/
            {c.golden_website_test.live_prices_de.business}/
            {c.golden_website_test.live_prices_de.premium} € (need 199/399/699)
          </p>
        ) : null}
      </section>

      <section className="rounded-xl border border-white/10 bg-black/20 p-4">
        <h2 className="text-sm font-semibold text-white">Company</h2>
        <div className="mt-3 grid gap-2 sm:grid-cols-4">
          {(
            [
              ["Golden Website", c?.golden_website_pct],
              ["Launch Readiness", c?.launch_readiness_pct],
              ["Performance", c?.performance_pct],
              ["Documentation", c?.documentation_pct],
            ] as const
          ).map(([label, pct]) => (
            <div key={label} className="rounded-lg border border-white/10 px-3 py-2">
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
              <p className="text-lg font-semibold text-white">{pct ?? 0}%</p>
            </div>
          ))}
        </div>
      </section>

      <p className="text-[11px] leading-relaxed text-zinc-500">{data?.kpi_law_ru}</p>

      <div className="flex flex-wrap gap-2 text-xs">
        <Link href="/farm-engine" className="text-amber-200/90 hover:underline">
          → Farm Engine
        </Link>
        <Link href="/clients" className="text-sky-200/90 hover:underline">
          → Clients
        </Link>
        <Link href="/ceo-site" className="text-emerald-200/90 hover:underline">
          → Site / Sales
        </Link>
      </div>
    </main>
  );
}
