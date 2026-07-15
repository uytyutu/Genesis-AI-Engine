"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { formatEur } from "../lib/formatEur";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Kpi = {
  current: number;
  target: number;
  auto: number;
  manual: number;
  progress_pct: number;
};

type Health = {
  mission: string;
  date: string;
  week_start: string;
  kpi_note_ru: string;
  kpis: Record<string, Kpi>;
  kpi_labels_ru: Record<string, string>;
  funnel_week: {
    companies_found: number;
    conversations: number;
    proposals: number;
    deals: number;
    revenue_eur: number;
    net_profit_eur: number;
  };
  weekly_review: {
    period_label_ru: string;
    best_seller_ru: string;
    worst_seller_ru: string;
    top_rejection_ru: string;
    top_rejection_count: number;
    recommendation_ru: string;
  };
  morning_brief: {
    headline_ru: string;
    lines_ru: { text: string; highlight: boolean }[];
    recommendation_ru: string;
  };
  market_signal: {
    opportunities_total: number;
    lost_reasons_logged: number;
    pipeline_active: number;
    data_honesty_ru: string;
  };
  links: Record<string, string>;
  ceo_outbox?: {
    title_ru: string;
    pending_count: number;
    outreach_send_enabled: boolean;
    money_path_ru: string;
    law_ru: string;
    items: {
      id: string;
      company_name?: string;
      website_url?: string;
      recommended_price_eur?: number;
      email_subject?: string;
      proposed_message?: string;
      score?: number;
    }[];
  };
};

const KPI_ORDER = ["conversations", "proposals", "payments", "repeats"] as const;

function KpiBar({ label, kpi }: { label: string; kpi: Kpi }) {
  return (
    <div className="rounded-xl border border-white/10 bg-genesis-bg/40 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm text-genesis-muted">{label}</p>
        <p className="text-xl font-semibold tabular-nums">
          {kpi.current}
          <span className="text-sm font-normal text-genesis-muted"> / {kpi.target}</span>
        </p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-emerald-500/80 transition-all"
          style={{ width: `${kpi.progress_pct}%` }}
        />
      </div>
      {kpi.manual > 0 ? (
        <p className="mt-2 text-xs text-genesis-muted">+{kpi.manual} вручную · {kpi.auto} из журнала</p>
      ) : (
        <p className="mt-2 text-xs text-genesis-muted">{kpi.auto} из журнала</p>
      )}
    </div>
  );
}

export default function BusinessHealthPage() {
  const [data, setData] = useState<Health | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [outboxMsg, setOutboxMsg] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/business-health`);
      if (res.ok) setData(await res.json());
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = setInterval(refresh, 20000);
    return () => clearInterval(t);
  }, [refresh]);

  const bump = async (field: (typeof KPI_ORDER)[number]) => {
    setBusy(field);
    try {
      const res = await fetch(`${API}/api/owner/business-health/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ field, delta: 1 }),
      });
      if (res.ok) setData(await res.json());
    } finally {
      setBusy(null);
    }
  };

  const approveAll = async () => {
    setBusy("outbox");
    setOutboxMsg("");
    try {
      const res = await fetch(`${API}/api/acquisition/approve-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 5 }),
      });
      const body = await res.json();
      setOutboxMsg(body.message_ru ?? "Готово");
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const prepareNow = async () => {
    setBusy("prepare");
    setOutboxMsg("");
    try {
      const res = await fetch(`${API}/api/acquisition/auto-prepare-discovery`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 3 }),
      });
      const body = await res.json();
      setOutboxMsg(body.message_ru ?? "Готово");
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const funnel = data?.funnel_week;
  const review = data?.weekly_review;
  const brief = data?.morning_brief;

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 via-genesis-panel to-genesis-bg p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold">Business Health</h1>
          <p className="mt-2 text-sm text-genesis-muted">{data?.mission ?? "Mission 2 — поиск рынка"}</p>
          {brief && (
            <div className="mt-5 rounded-xl border border-white/5 bg-genesis-bg/50 p-4">
              <p className="text-lg font-medium">{brief.headline_ru}</p>
              <ul className="mt-3 space-y-1.5 text-sm">
                {brief.lines_ru.map((line) => (
                  <li key={line.text} className={line.highlight ? "text-emerald-300" : "text-genesis-muted"}>
                    {line.text}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm font-medium text-emerald-200">{brief.recommendation_ru}</p>
            </div>
          )}
        </header>

        {data?.ceo_outbox && (
          <section className="rounded-2xl border border-amber-500/30 bg-amber-950/15 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">{data.ceo_outbox.title_ru}</h2>
                <p className="mt-1 text-sm text-genesis-muted">{data.ceo_outbox.money_path_ru}</p>
                <p className="mt-2 text-xs text-amber-200/80">{data.ceo_outbox.law_ru}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => void prepareNow()}
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-sm hover:bg-white/5 disabled:opacity-50"
                >
                  {busy === "prepare" ? "…" : "Подготовить лиды"}
                </button>
                {data.ceo_outbox.pending_count > 0 && (
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void approveAll()}
                    className="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    {busy === "outbox" ? "…" : `Одобрить все (${data.ceo_outbox.pending_count})`}
                  </button>
                )}
              </div>
            </div>
            {outboxMsg ? <p className="mt-3 text-sm text-emerald-300">{outboxMsg}</p> : null}
            {data.ceo_outbox.items.length > 0 ? (
              <ul className="mt-4 space-y-3">
                {data.ceo_outbox.items.map((item) => (
                  <li key={item.id} className="rounded-xl border border-white/10 bg-genesis-bg/40 p-4 text-sm">
                    <p className="font-medium">
                      {item.company_name ?? "Лид"} · {formatEur(item.recommended_price_eur ?? 0)}
                      {item.score != null ? ` · score ${item.score}` : ""}
                    </p>
                    {item.website_url ? (
                      <p className="mt-1 truncate text-xs text-genesis-muted">{item.website_url}</p>
                    ) : null}
                    {item.email_subject ? (
                      <p className="mt-2 text-xs text-emerald-200/90">Тема: {item.email_subject}</p>
                    ) : null}
                    {item.proposed_message ? (
                      <p className="mt-2 line-clamp-3 text-xs text-genesis-muted whitespace-pre-wrap">
                        {item.proposed_message}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-genesis-muted">
                Очередь пуста. Запустите ферму — письма подготовятся автоматически (раз в ~20 мин) или нажмите
                «Подготовить лиды».
              </p>
            )}
            <p className="mt-4 text-xs text-genesis-muted">
              Биржа Toloka (112 € в журнале) — не этот путь. Реальные € = оплата клиента →{" "}
              <Link href="/finance" className="text-emerald-400 underline">
                Финансы
              </Link>
              .
            </p>
          </section>
        )}

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-genesis-muted">Цели Mission 2</h2>
            <div className="flex gap-2 text-xs">
              <Link href={data?.links.farm ?? "/"} className="rounded-lg border border-white/10 px-2 py-1 hover:bg-white/5">
                Ферма
              </Link>
              <Link href={data?.links.journal ?? "/journal"} className="rounded-lg border border-white/10 px-2 py-1 hover:bg-white/5">
                Журнал
              </Link>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {KPI_ORDER.map((key) => {
              const kpi = data?.kpis[key];
              if (!kpi) return null;
              return (
                <div key={key} className="relative">
                  <KpiBar label={data?.kpi_labels_ru[key] ?? key} kpi={kpi} />
                  <button
                    type="button"
                    disabled={busy === key}
                    onClick={() => void bump(key)}
                    className="absolute right-3 top-3 rounded-md border border-emerald-500/30 px-2 py-0.5 text-xs text-emerald-200 hover:bg-emerald-950/40 disabled:opacity-50"
                    title="Полевой звонок вне журнала"
                  >
                    +1
                  </button>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-genesis-muted">{data?.kpi_note_ru}</p>
        </section>

        {funnel && (
          <section className="rounded-2xl border border-white/10 bg-genesis-panel/50 p-6">
            <h2 className="text-sm font-medium uppercase tracking-wider text-genesis-muted">
              Воронка · неделя с {data?.week_start}
            </h2>
            <div className="mt-5 flex flex-col items-center gap-1 text-center">
              {[
                { n: funnel.companies_found, label: "компаний найдено" },
                { n: funnel.conversations, label: "разговоров" },
                { n: funnel.proposals, label: "предложений" },
                { n: funnel.deals, label: "договоров" },
                { n: formatEur(funnel.revenue_eur), label: "выручка" },
                { n: formatEur(funnel.net_profit_eur), label: "чистая прибыль" },
              ].map((step, i, arr) => (
                <div key={step.label} className="w-full">
                  <p className="text-2xl font-semibold tabular-nums">{step.n}</p>
                  <p className="text-xs text-genesis-muted">{step.label}</p>
                  {i < arr.length - 1 ? <p className="my-1 text-genesis-muted">↓</p> : null}
                </div>
              ))}
            </div>
          </section>
        )}

        {review && (
          <section className="rounded-2xl border border-white/10 bg-genesis-panel/50 p-6">
            <h2 className="text-sm font-medium uppercase tracking-wider text-genesis-muted">Weekly Review</h2>
            <p className="mt-1 text-xs text-genesis-muted">{review.period_label_ru} · без ИИ, только факты</p>
            <div className="mt-5 space-y-4 text-sm">
              <div>
                <p className="text-genesis-muted">Лучше всего продавалась</p>
                <p className="font-medium text-emerald-300">{review.best_seller_ru}</p>
              </div>
              <p className="text-center text-genesis-muted">↓</p>
              <div>
                <p className="text-genesis-muted">Хуже всего</p>
                <p className="font-medium">{review.worst_seller_ru}</p>
              </div>
              <p className="text-center text-genesis-muted">↓</p>
              <div>
                <p className="text-genesis-muted">Главная причина отказов</p>
                <p className="font-medium">
                  {review.top_rejection_ru}
                  {review.top_rejection_count > 0 ? ` (${review.top_rejection_count})` : ""}
                </p>
              </div>
              <p className="text-center text-genesis-muted">↓</p>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4">
                <p className="text-xs uppercase tracking-wider text-emerald-400/80">Рекомендация</p>
                <p className="mt-2 font-medium">{review.recommendation_ru}</p>
              </div>
            </div>
          </section>
        )}

        {data?.market_signal && (
          <p className="text-center text-xs text-genesis-muted">
            {data.market_signal.data_honesty_ru} · в журнале {data.market_signal.opportunities_total} · в работе{" "}
            {data.market_signal.pipeline_active}
          </p>
        )}
      </div>
    </main>
  );
}
