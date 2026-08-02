"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type FarmMaturity = {
  title_ru?: string;
  law_ru?: string;
  estimate_vs_real_ru?: string;
  live_connector_allowed?: boolean;
  income_phase?: {
    phase?: string;
    is_modeling?: boolean;
    real_income_possible?: boolean;
    law_ru?: string;
  };
  commercial_blocker?: {
    why_real_zero_ru?: string;
    question_right_ru?: string;
    next_ru?: string;
    checklist?: { id: string; title_ru: string; ok: boolean; value_eur?: number }[];
    first_live_earn_candidates?: {
      id: string;
      title_ru: string;
      why_ru: string;
      status?: string;
    }[];
    not_earn_ru?: { id: string; title_ru: string; note_ru: string }[];
  };
  levels?: {
    id: string;
    title_ru: string;
    status_ru: string;
    detail_ru: string;
  }[];
  live_gates?: {
    id: string;
    title_ru: string;
    ok: boolean;
    note_ru: string;
  }[];
  kpi?: {
    research?: number;
    go?: number;
    prototype?: number;
    confirmed_eur?: number;
    funnel_ru?: string[];
    commercial_when_ru?: string;
  };
  factory?: {
    identity_ru?: string;
    north_star_ru?: string;
    separation_ru?: string;
    gap_ru?: string;
    cannot_ru?: string[];
    value_chain?: string[];
    layers?: {
      id: string;
      title_en?: string;
      title_ru?: string;
      note_ru?: string;
      items?: { id?: string; label?: string; title?: string }[];
    }[];
  };
  distribution?: {
    title_ru?: string;
    status_ru?: string;
    independent_of_factory_ru?: string;
    next_ru?: string;
    without_distribution_ru?: string;
    with_distribution_ru?: string;
    finance_gate_ru?: string;
    example_product_channels_ru?: string;
    platform_earn_criteria?: { id?: string; title_ru?: string }[];
    groups?: {
      id: string;
      title_en?: string;
      title_ru?: string;
      channels?: { id?: string; label?: string }[];
    }[];
  };
};

type Props = {
  data?: FarmMaturity | null;
  /** If true, fetch /api/farm/engine/v1 when data not passed */
  autoFetch?: boolean;
  compact?: boolean;
};

export function FarmMaturityBoard({ data: initial, autoFetch = false, compact }: Props) {
  const [data, setData] = useState<FarmMaturity | null>(initial ?? null);

  const refresh = useCallback(async () => {
    if (!autoFetch && initial) {
      setData(initial);
      return;
    }
    try {
      const res = await fetch(`${API}/api/farm/engine/v1`);
      if (!res.ok) return;
      const body = await res.json();
      setData(body.maturity ?? null);
    } catch {
      /* ignore */
    }
  }, [autoFetch, initial]);

  useEffect(() => {
    if (initial) setData(initial);
  }, [initial]);

  useEffect(() => {
    if (!autoFetch) return;
    void refresh();
    const t = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(t);
  }, [autoFetch, refresh]);

  if (!data) return null;

  const kpi = data.kpi || {};
  const gates = data.live_gates || [];
  const levels = data.levels || [];

  return (
    <section
      className={`rounded-xl border border-violet-500/30 bg-violet-950/15 ${
        compact ? "p-4" : "p-5"
      } space-y-4`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-violet-100">
            {data.title_ru ?? "Зрелость · Commercial vs Farm vs Earn"}
          </h2>
          <p className="mt-1 text-xs text-genesis-muted">{data.law_ru}</p>
        </div>
        <Link
          href="/farm-engine"
          className="rounded-lg border border-violet-400/30 px-2.5 py-1 text-[11px] text-violet-100 hover:bg-violet-950/40"
        >
          Farm Engine →
        </Link>
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        {levels.map((lv) => (
          <div
            key={lv.id}
            className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs"
          >
            <p className="font-medium text-white/90">{lv.title_ru}</p>
            <p className="mt-1 text-violet-100/90">{lv.status_ru}</p>
            <p className="mt-1 text-[11px] text-genesis-muted">{lv.detail_ru}</p>
          </div>
        ))}
      </div>

      {data.factory?.layers?.length ? (
        <div>
          <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
            OS цифровых сервисов
          </p>
          <p className="mt-1 text-[11px] text-white/70">
            {data.factory.identity_ru ?? data.factory.north_star_ru}
          </p>
          <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {data.factory.layers.map((layer) => (
              <div
                key={layer.id}
                className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs"
              >
                <p className="font-medium text-white/90">
                  {layer.title_ru ?? layer.title_en}
                </p>
                {layer.note_ru ? (
                  <p className="mt-0.5 text-[10px] text-violet-100/70">{layer.note_ru}</p>
                ) : null}
                <p className="mt-1 text-[11px] leading-relaxed text-genesis-muted">
                  {(layer.items || [])
                    .slice(0, compact ? 3 : 6)
                    .map((it) => it.label || it.title || it.id)
                    .filter(Boolean)
                    .join(" · ")}
                  {(layer.items || []).length > (compact ? 3 : 6) ? " · …" : ""}
                </p>
              </div>
            ))}
          </div>
          {!compact && data.factory.separation_ru ? (
            <p className="mt-2 text-[11px] text-genesis-muted">
              {data.factory.separation_ru}
            </p>
          ) : null}
          {!compact && data.factory.gap_ru ? (
            <p className="mt-1 text-[11px] text-amber-100/80">{data.factory.gap_ru}</p>
          ) : null}
        </div>
      ) : null}

      {data.distribution ? (
        <div className="rounded-lg border border-sky-500/25 bg-sky-950/15 px-3 py-2 text-xs">
          <p className="font-medium text-sky-100">
            {data.distribution.title_ru ?? "Distribution"}
          </p>
          <p className="mt-1 text-sky-100/90">
            {data.distribution.status_ru}
          </p>
          <p className="mt-1 text-[11px] text-genesis-muted">
            {data.distribution.independent_of_factory_ru}
          </p>
          {data.distribution.groups?.length ? (
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {data.distribution.groups.map((g) => (
                <div
                  key={g.id}
                  className="rounded border border-sky-400/20 bg-black/20 px-2 py-1.5"
                >
                  <p className="text-[11px] font-medium text-sky-50">
                    {g.title_ru ?? g.title_en}
                  </p>
                  <p className="mt-0.5 text-[10px] text-genesis-muted">
                    {(g.channels || []).map((c) => c.label || c.id).join(" · ")}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
          {!compact && data.distribution.example_product_channels_ru ? (
            <p className="mt-2 text-[11px] text-white/70">
              {data.distribution.example_product_channels_ru}
            </p>
          ) : null}
          {!compact && data.distribution.platform_earn_criteria?.length ? (
            <ul className="mt-2 list-disc space-y-0.5 pl-4 text-[11px] text-white/70">
              {data.distribution.platform_earn_criteria.map((c) => (
                <li key={c.id}>{c.title_ru}</li>
              ))}
            </ul>
          ) : null}
          <p className="mt-2 text-[11px] text-white/75">
            {data.distribution.without_distribution_ru} ·{" "}
            {data.distribution.with_distribution_ru}
          </p>
          {!compact && data.distribution.finance_gate_ru ? (
            <p className="mt-1 text-[11px] text-amber-100/80">
              {data.distribution.finance_gate_ru}
            </p>
          ) : null}
          {!compact && data.distribution.next_ru ? (
            <p className="mt-1 text-[11px] text-sky-100/80">
              {data.distribution.next_ru}
            </p>
          ) : null}
        </div>
      ) : null}

      <div>
        <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
          KPI фермы (не «найдено возможностей»)
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          {(kpi.funnel_ru || ["Research", "GO", "Prototype", "Confirmed €"]).map((step, i) => {
            const vals = [
              kpi.research ?? 0,
              kpi.go ?? 0,
              kpi.prototype ?? 0,
              kpi.confirmed_eur ?? 0,
            ];
            const label =
              i === 3 ? `${Number(vals[i]).toFixed(2)} €` : String(vals[i] ?? 0);
            return (
              <span key={step} className="flex items-center gap-2">
                {i > 0 ? <span className="text-white/30">↓</span> : null}
                <span className="rounded-lg border border-white/15 bg-black/30 px-2.5 py-1">
                  <span className="text-[10px] text-genesis-muted">{step}</span>
                  <span className="ml-2 font-semibold tabular-nums text-white">{label}</span>
                </span>
              </span>
            );
          })}
        </div>
        <p className="mt-2 text-[11px] text-genesis-muted">{kpi.commercial_when_ru}</p>
      </div>

      <div>
        <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
          Live Connector — четыре Gate (все обязательны)
        </p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {gates.map((g) => (
            <div
              key={g.id}
              className={`rounded-lg border px-3 py-2 text-xs ${
                g.ok
                  ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-100"
                  : "border-amber-500/30 bg-amber-950/20 text-amber-100"
              }`}
            >
              <p className="font-medium">
                {g.ok ? "PASS" : "WAIT"} · {g.title_ru}
              </p>
              <p className="mt-0.5 text-[11px] opacity-80">{g.note_ru}</p>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-white/80">
          Live Connector:{" "}
          {data.live_connector_allowed
            ? "разрешён (все Gate PASS)"
            : "закрыт — нет Confirmed € PASS"}
        </p>
      </div>

      {data.income_phase ? (
        <p
          className={`rounded-lg border px-3 py-2 text-[11px] leading-relaxed ${
            data.income_phase.is_modeling
              ? "border-amber-500/25 bg-amber-950/20 text-amber-100/90"
              : "border-emerald-500/25 bg-emerald-950/20 text-emerald-100/90"
          }`}
        >
          {data.income_phase.is_modeling
            ? "Фаза: моделирование — реального дохода ещё нет."
            : "Фаза: real_eligible — Live Earn + выплаты подтверждены."}{" "}
          {data.income_phase.law_ru}
        </p>
      ) : null}

      {data.commercial_blocker ? (
        <div className="rounded-lg border border-rose-500/25 bg-rose-950/15 px-3 py-2 text-xs space-y-2">
          <p className="font-medium text-rose-100">Почему REAL = 0 · главный блокер</p>
          <p className="text-[11px] text-white/80">
            {data.commercial_blocker.why_real_zero_ru}
          </p>
          {data.commercial_blocker.checklist?.length ? (
            <ul className="space-y-0.5 text-[11px]">
              {data.commercial_blocker.checklist.map((c) => (
                <li key={c.id} className="flex justify-between gap-2">
                  <span className="text-white/75">{c.title_ru}</span>
                  <span className={c.ok ? "text-emerald-300" : "text-rose-300"}>
                    {c.id === "real_eur"
                      ? `${Number(c.value_eur ?? 0).toFixed(2)} €`
                      : c.ok
                        ? "✅"
                        : "❌"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
          {data.commercial_blocker.not_earn_ru?.length ? (
            <div className="text-[11px] text-amber-100/85">
              {data.commercial_blocker.not_earn_ru.map((n) => (
                <p key={n.id} className="mt-1">
                  <span className="font-medium">{n.title_ru}</span> — {n.note_ru}
                </p>
              ))}
            </div>
          ) : null}
          {data.commercial_blocker.first_live_earn_candidates?.length ? (
            <div>
              <p className="text-[11px] uppercase tracking-wide text-genesis-muted">
                Кандидаты на первый Live Earn
              </p>
              <ul className="mt-1 space-y-1 text-[11px] text-white/80">
                {data.commercial_blocker.first_live_earn_candidates.map((c) => (
                  <li key={c.id}>
                    <span className="font-medium text-white/90">{c.title_ru}</span>
                    {" — "}
                    {c.why_ru}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <p className="text-[11px] font-medium text-rose-50">
            {data.commercial_blocker.question_right_ru}
          </p>
          {!compact && data.commercial_blocker.next_ru ? (
            <p className="text-[11px] text-genesis-muted">
              {data.commercial_blocker.next_ru}
            </p>
          ) : null}
        </div>
      ) : null}

      <p className="rounded-lg border border-amber-500/25 bg-amber-950/20 px-3 py-2 text-[11px] leading-relaxed text-amber-100/90">
        {data.estimate_vs_real_ru}
      </p>
    </section>
  );
}
