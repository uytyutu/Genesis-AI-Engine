"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Metric = {
  id: string;
  label: string;
  value?: number | string | null;
  unit?: string;
  coming?: string;
};

type Section = {
  id: string;
  label: string;
  status?: string;
  coming?: string;
  metrics: Metric[];
};

type ProviderCount = {
  id: string;
  category: string;
  label: string;
  connected_stores: number;
};

type Gen1Item = {
  id: string;
  label: string;
  status: string;
  detail?: string;
};

type GlobalAnalytics = {
  title: string;
  subtitle?: string;
  headline?: Record<string, number | null | undefined>;
  sections: Section[];
  integrations?: {
    stores_scanned: number;
    commerce_incomplete_stores: number;
    providers: ProviderCount[];
    privacy?: string;
  };
  revenue?: {
    title: string;
    periods: Record<string, number | null | undefined>;
    metrics: Record<string, number | null | undefined>;
    note?: string;
  };
  funnel?: {
    title: string;
    subtitle?: string;
    stages: { id: string; label: string; count?: number | null }[];
    biggest_drop?: {
      from?: string;
      to?: string;
      lost_pct?: number;
      question?: string;
    } | null;
    note?: string;
  };
  gen1_readiness?: {
    title: string;
    done: number;
    total: number;
    pct: number;
    next?: Gen1Item | null;
    items: Gen1Item[];
    focus?: string;
    phase?: string;
  };
  launch_readiness?: {
    title: string;
    done: number;
    total: number;
    pct: number;
    next?: Gen1Item | null;
    items: Gen1Item[];
    focus?: string;
    phase?: string;
    beta_clients?: number;
    note?: string;
  };
  business_kpis?: {
    title?: string;
    subtitle?: string;
    done?: number;
    total?: number;
    items?: Gen1Item[];
    focus?: string;
    next?: Gen1Item | null;
    primary_kpi?: string;
  };
  sales_focus?: {
    title?: string;
    subtitle?: string;
    goal?: number;
    count?: number;
    remaining?: number;
    pct?: number;
    on_goal?: boolean;
    focus?: string;
    path?: string[];
    target_niches?: { id: string; label: string }[];
    after_each_sale?: string[];
    clients?: {
      id?: string;
      niche?: string | null;
      kind?: string;
      paid_at?: string;
    }[];
  };
  time_to_launch?: {
    title?: string;
    subtitle?: string;
    focus?: string;
    website?: {
      median_min?: number | null;
      goal_min?: number;
      on_goal?: boolean | null;
      status?: string;
      detail?: string;
      samples?: number;
    };
    store?: {
      median_min?: number | null;
      goal_min?: number;
      on_goal?: boolean | null;
      status?: string;
      detail?: string;
      samples?: number;
    };
  };
  first_value_time?: {
    title?: string;
    subtitle?: string;
    focus?: string;
    median_min?: number | null;
    avg_min?: number | null;
    goal_min?: number;
    on_goal?: boolean | null;
    status?: string;
    detail?: string;
    samples?: number;
    by_kind?: Record<string, number>;
  };
  email?: {
    title?: string;
    connected?: number;
    test_success_rate?: number | null;
    failed_sends?: number;
    queued?: number;
    last_error?: string | null;
  };
  shipping?: {
    title?: string;
    dhl?: number;
    dpd?: number;
    gls?: number;
    hermes?: number;
    ups?: number;
    fedex?: number;
    shipments_created?: number;
    delivered?: number;
    api_errors?: number;
    stores_with_api?: number;
  };
  note?: string;
};

function fmt(v: number | string | null | undefined, unit?: string) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") {
    const n = Number.isInteger(v) ? String(v) : v.toFixed(2);
    return unit ? `${n} ${unit}` : n;
  }
  return String(v);
}

export default function GlobalAnalyticsPage() {
  const [data, setData] = useState<GlobalAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/global-analytics`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = setInterval(() => void refresh(), 30000);
    return () => clearInterval(t);
  }, [refresh]);

  const h = data?.headline || {};
  const integ = data?.integrations;
  const rev = data?.revenue;
  const funnel = data?.funnel;
  const gen1 = data?.gen1_readiness;
  const launch = data?.launch_readiness;
  const bizKpis = data?.business_kpis;
  const salesFocus = data?.sales_focus;
  const ttl = data?.time_to_launch;
  const fvt = data?.first_value_time;
  const emailStats = data?.email;
  const shippingStats = data?.shipping;

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/25 via-genesis-panel to-genesis-bg p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">
                {BRAND_NAME} · Mission Control
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                {data?.title || "Global Analytics"}
              </h1>
              <p className="mt-1 max-w-2xl text-sm text-genesis-muted">
                {data?.subtitle ||
                  "Единый центр управления бизнесом — финансы, продукты, Commerce, Factory, Apify."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href="/executive"
                className="rounded-lg border border-emerald-400/40 bg-emerald-950/30 px-3 py-1.5 text-sm text-emerald-100 hover:bg-emerald-950/50"
              >
                CEO Dashboard
              </Link>
              <Link
                href="/"
                className="rounded-lg border border-genesis-border px-3 py-1.5 text-sm hover:bg-genesis-elevated/40"
              >
                ← Mission Control
              </Link>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Выручка сегодня", h.revenue_today_eur, "€"],
              ["Новые клиенты", h.new_clients, ""],
              ["Магазины с интеграциями", h.stores_with_integrations, ""],
              ["Commerce не завершён", h.commerce_incomplete, ""],
            ].map(([label, value, unit]) => (
              <div
                key={String(label)}
                className="rounded-xl border border-white/10 bg-black/20 px-4 py-3"
              >
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                  {label}
                </p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {fmt(value as number | null | undefined, unit as string)}
                </p>
              </div>
            ))}
          </div>
        </header>

        {error ? (
          <p className="text-sm text-rose-400" role="alert">
            {error}
          </p>
        ) : null}

        {launch ? (
          <section className="rounded-2xl border border-violet-500/30 bg-violet-950/10 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-300/80">
                  Feature Freeze → Public Launch
                </p>
                <h2 className="mt-1 text-lg font-semibold">
                  {launch.title || "Launch Readiness"}
                </h2>
                <p className="mt-1 text-xs text-genesis-muted">
                  {launch.focus ||
                    "Performance · Beta Feedback · Docs — then Launch Ready."}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-right">
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                  Progress
                </p>
                <p className="text-xl font-semibold text-violet-100">
                  {launch.done}/{launch.total} · {launch.pct}%
                </p>
              </div>
            </div>
            {launch.next ? (
              <p className="text-sm text-violet-100/90">
                Next: <span className="font-semibold">{launch.next.label}</span>
                {launch.next.detail ? (
                  <span className="text-genesis-muted"> — {launch.next.detail}</span>
                ) : null}
              </p>
            ) : null}
            <ul className="grid gap-1.5 sm:grid-cols-2">
              {(launch.items || []).map((item) => {
                const done = item.status === "done";
                return (
                  <li
                    key={item.id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
                  >
                    <span className="text-genesis-muted" title={item.detail || undefined}>
                      {item.label}
                    </span>
                    <span
                      className={
                        done ? "font-semibold text-emerald-300" : "font-semibold text-amber-200"
                      }
                    >
                      {done ? "✅" : "⏳"}
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}

        {salesFocus ? (
          <section className="rounded-2xl border border-amber-500/30 bg-amber-950/15 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-300/80">
                  Priority #1 · Sales
                </p>
                <h2 className="mt-1 text-lg font-semibold">
                  {salesFocus.title || "First 5 Clients"}
                </h2>
                <p className="mt-1 text-xs text-genesis-muted">
                  {salesFocus.subtitle ||
                    "Главный приоритет: продажи. Каждый клиент = реальная Beta."}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-right">
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                  Clients
                </p>
                <p className="text-xl font-semibold text-amber-100">
                  {salesFocus.count ?? 0}/{salesFocus.goal ?? 5}
                </p>
              </div>
            </div>
            {salesFocus.path?.length ? (
              <p className="text-xs text-amber-100/80">
                {salesFocus.path.join(" → ")}
              </p>
            ) : null}
            <ul className="grid gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
              {(salesFocus.target_niches || []).map((n) => (
                <li
                  key={n.id}
                  className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-genesis-muted"
                >
                  {n.label}
                </li>
              ))}
            </ul>
            {salesFocus.after_each_sale?.length ? (
              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-genesis-muted space-y-1">
                <p className="font-medium text-white/80">После каждой продажи:</p>
                {salesFocus.after_each_sale.map((q) => (
                  <p key={q}>• {q}</p>
                ))}
              </div>
            ) : null}
            {salesFocus.focus ? (
              <p className="text-xs text-genesis-muted">{salesFocus.focus}</p>
            ) : null}
          </section>
        ) : null}

        {bizKpis ? (
          <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/10 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-300/80">
                  Primary KPI
                </p>
                <h2 className="mt-1 text-lg font-semibold">
                  {bizKpis.title || "Success Path"}
                </h2>
                <p className="mt-1 text-xs text-genesis-muted">
                  {bizKpis.subtitle ||
                    "Сколько успешных клиентов прошло полный путь."}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-right">
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                  Path
                </p>
                <p className="text-xl font-semibold text-emerald-100">
                  {bizKpis.done ?? 0}/{bizKpis.total ?? 0}
                </p>
              </div>
            </div>
            {bizKpis.next ? (
              <p className="text-sm text-emerald-100/90">
                Next: <span className="font-semibold">{bizKpis.next.label}</span>
                {bizKpis.next.detail ? (
                  <span className="text-genesis-muted"> — {bizKpis.next.detail}</span>
                ) : null}
              </p>
            ) : null}
            <ul className="grid gap-1.5 sm:grid-cols-2">
              {(bizKpis.items || []).map((item) => {
                const done = item.status === "done";
                return (
                  <li
                    key={item.id}
                    className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium text-white/90">{item.label}</span>
                      <span className={done ? "text-emerald-300" : "text-amber-200"}>
                        {done ? "✅" : "⏳"}
                      </span>
                    </div>
                    {item.detail ? (
                      <p className="mt-1 text-[11px] text-genesis-muted">{item.detail}</p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}

        {ttl ? (
          <section className="rounded-2xl border border-cyan-500/25 bg-cyan-950/10 p-5 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">{ttl.title || "Time To Launch"}</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                {ttl.subtitle || ttl.focus || "От покупки до публикации."}
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ["Website", ttl.website, "< 30 мин"],
                ["AI Store", ttl.store, "< 60 мин"],
              ].map(([label, block, goal]) => {
                const b = block as
                  | {
                      median_min?: number | null;
                      detail?: string;
                      on_goal?: boolean | null;
                      samples?: number;
                    }
                  | undefined;
                return (
                  <div
                    key={String(label)}
                    className="rounded-xl border border-white/10 bg-black/20 px-4 py-3"
                  >
                    <p className="text-[11px] uppercase text-genesis-muted">
                      {String(label)} · цель {String(goal)}
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-white">
                      {b?.median_min == null ? "—" : `${b.median_min} мин`}
                    </p>
                    <p className="mt-1 text-[11px] text-genesis-muted">
                      {b?.detail || "Нет измерений"}
                      {b?.samples ? ` · n=${b.samples}` : ""}
                    </p>
                  </div>
                );
              })}
            </div>
          </section>
        ) : null}

        {fvt ? (
          <section className="rounded-2xl border border-sky-500/25 bg-sky-950/10 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-sky-300/80">
                  Retention signal
                </p>
                <h2 className="mt-1 text-lg font-semibold">
                  {fvt.title || "First Value Time"}
                </h2>
                <p className="mt-1 text-xs text-genesis-muted max-w-2xl">
                  {fvt.subtitle ||
                    "От покупки до первой реальной пользы для клиента."}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-right">
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                  Медиана · цель &lt; {fvt.goal_min ?? 60} мин
                </p>
                <p className="text-xl font-semibold text-sky-100">
                  {fvt.median_min == null ? "—" : `${fvt.median_min} мин`}
                </p>
              </div>
            </div>
            <p className="text-sm text-sky-100/90">
              {fvt.detail || fvt.focus || "Нет измерений"}
              {fvt.samples ? (
                <span className="text-genesis-muted"> · n={fvt.samples}</span>
              ) : null}
            </p>
            {fvt.by_kind && Object.keys(fvt.by_kind).length > 0 ? (
              <ul className="flex flex-wrap gap-2 text-xs text-genesis-muted">
                {Object.entries(fvt.by_kind).map(([k, n]) => (
                  <li
                    key={k}
                    className="rounded-lg border border-white/10 bg-black/20 px-2 py-1"
                  >
                    {k}: {n}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {gen1 ? (
          <section className="rounded-2xl border border-amber-500/30 bg-amber-950/10 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">{gen1.title || "Gen1 Readiness"}</h2>
                <p className="mt-1 text-xs text-genesis-muted">
                  {gen1.focus || "Close real integrations → premium visuals → first clients."}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-right">
                <p className="text-[11px] uppercase tracking-wide text-genesis-muted">Progress</p>
                <p className="text-xl font-semibold text-amber-100">
                  {gen1.done}/{gen1.total} · {gen1.pct}%
                </p>
              </div>
            </div>
            {gen1.next ? (
              <p className="text-sm text-amber-100/90">
                Next: <span className="font-semibold">{gen1.next.label}</span>
                {gen1.next.detail ? (
                  <span className="text-genesis-muted"> — {gen1.next.detail}</span>
                ) : null}
              </p>
            ) : null}
            <ul className="grid gap-1.5 sm:grid-cols-2">
              {(gen1.items || []).map((item) => {
                const done = item.status === "done";
                return (
                  <li
                    key={item.id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
                  >
                    <span className="text-genesis-muted">{item.label}</span>
                    <span
                      className={
                        done ? "font-semibold text-emerald-300" : "font-semibold text-amber-200"
                      }
                      title={item.detail || undefined}
                    >
                      {done ? "✅" : "⏳"}
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}

        {emailStats ? (
          <section className="rounded-2xl border border-sky-500/25 bg-sky-950/10 p-5 space-y-4">
            <h2 className="text-lg font-semibold">{emailStats.title || "Email"}</h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              {[
                ["Connected", emailStats.connected],
                [
                  "Test Success Rate",
                  emailStats.test_success_rate == null
                    ? "—"
                    : `${emailStats.test_success_rate}%`,
                ],
                ["Failed Sends", emailStats.failed_sends],
                ["Queued", emailStats.queued],
                ["Last Error", emailStats.last_error || "—"],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-2"
                >
                  <p className="text-[11px] uppercase text-genesis-muted">{label}</p>
                  <p className="mt-1 text-sm font-semibold truncate">{fmt(value as never)}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {shippingStats ? (
          <section className="rounded-2xl border border-teal-500/25 bg-teal-950/10 p-5 space-y-4">
            <h2 className="text-lg font-semibold">{shippingStats.title || "Shipping"}</h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["DHL stores", shippingStats.dhl],
                ["DPD stores", shippingStats.dpd],
                ["GLS stores", shippingStats.gls],
                ["Hermes stores", shippingStats.hermes],
                ["Shipments created", shippingStats.shipments_created],
                ["Delivered", shippingStats.delivered],
                ["API errors", shippingStats.api_errors],
                ["Stores with API", shippingStats.stores_with_api],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-2"
                >
                  <p className="text-[11px] uppercase text-genesis-muted">{label}</p>
                  <p className="mt-1 text-sm font-semibold truncate">{fmt(value as never)}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {rev ? (
          <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/10 p-5 space-y-4">
            <h2 className="text-lg font-semibold">{rev.title || "Revenue Dashboard"}</h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Сегодня", rev.periods?.today_eur],
                ["Неделя", rev.periods?.week_eur],
                ["Месяц", rev.periods?.month_eur],
                ["Год", rev.periods?.year_eur],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-2"
                >
                  <p className="text-[11px] uppercase text-genesis-muted">{label}</p>
                  <p className="text-lg font-semibold">{fmt(value as number | null, "€")}</p>
                </div>
              ))}
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {[
                ["MRR", rev.metrics?.mrr_eur, "€"],
                ["ARR", rev.metrics?.arr_eur, "€"],
                ["Средний чек", rev.metrics?.avg_order_eur, "€"],
                ["LTV", rev.metrics?.ltv_eur, "€"],
                ["CAC", rev.metrics?.cac_eur, "€"],
                ["Conversion", rev.metrics?.conversion_pct, "%"],
                ["Refunds", rev.metrics?.refunds_eur, "€"],
                ["Pending", rev.metrics?.pending_orders, ""],
                ["Completed", rev.metrics?.completed_orders, ""],
                ["Shop GMV", rev.metrics?.shop_gmv_eur, "€"],
              ].map(([label, value, unit]) => (
                <div
                  key={String(label)}
                  className="flex justify-between gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm"
                >
                  <span className="text-genesis-muted">{label}</span>
                  <span className="font-medium">{fmt(value as number | null, unit as string)}</span>
                </div>
              ))}
            </div>
            {rev.note ? <p className="text-xs text-genesis-muted">{rev.note}</p> : null}
          </section>
        ) : null}

        {funnel ? (
          <section className="rounded-2xl border border-violet-500/25 bg-violet-950/10 p-5 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">{funnel.title || "Daily Funnel"}</h2>
              {funnel.subtitle ? (
                <p className="mt-1 text-xs text-genesis-muted">{funnel.subtitle}</p>
              ) : null}
            </div>
            {funnel.biggest_drop?.question ? (
              <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-sm text-amber-100">
                {funnel.biggest_drop.question}
              </p>
            ) : null}
            <ol className="space-y-2">
              {(funnel.stages || []).map((s, i) => (
                <li
                  key={s.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
                >
                  <span>
                    <span className="mr-2 text-genesis-muted">{i + 1}.</span>
                    {s.label}
                  </span>
                  <span className="font-semibold text-violet-200">
                    {s.count == null ? "—" : s.count}
                  </span>
                </li>
              ))}
            </ol>
            {funnel.note ? <p className="text-xs text-genesis-muted">{funnel.note}</p> : null}
          </section>
        ) : null}

        {integ ? (
          <section className="rounded-2xl border border-sky-500/25 bg-sky-950/10 p-5 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">Integrations Analytics</h2>
              <p className="text-xs text-genesis-muted">
                {integ.privacy || "Aggregated connection status — no buyer PII."}
              </p>
            </div>
            <p className="text-sm text-genesis-muted">
              Stores scanned: <strong className="text-white">{integ.stores_scanned}</strong>
              {" · "}
              Incomplete Commerce:{" "}
              <strong className="text-amber-200">{integ.commerce_incomplete_stores}</strong>
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {(integ.providers || []).slice(0, 12).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
                >
                  <span>
                    {p.label}
                    <span className="ml-2 text-[10px] uppercase text-genesis-muted">
                      {p.category}
                    </span>
                  </span>
                  <span className="font-semibold text-emerald-300">{p.connected_stores}</span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {(data?.sections || []).map((section) => (
            <section
              key={section.id}
              className="rounded-2xl border border-white/10 bg-genesis-panel/60 p-5"
            >
              <div className="flex items-baseline justify-between gap-2">
                <h2 className="text-base font-semibold">{section.label}</h2>
                <span className="text-[10px] uppercase tracking-wide text-genesis-muted">
                  {section.coming || section.status || ""}
                </span>
              </div>
              <ul className="mt-3 space-y-2">
                {(section.metrics || []).map((m) => (
                  <li
                    key={m.id}
                    className="flex items-center justify-between gap-3 text-sm"
                  >
                    <span className="text-genesis-muted">{m.label}</span>
                    <span className="font-medium text-white">
                      {m.coming ? `Coming ${m.coming}` : fmt(m.value, m.unit)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        {data?.note ? (
          <p className="text-center text-xs text-genesis-muted">{data.note}</p>
        ) : null}
      </div>
    </main>
  );
}
