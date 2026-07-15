"use client";

import Link from "next/link";

export type MoneyMonitorLane = {
  id: string;
  icon: string;
  label_ru: string;
  amount_label_ru: string;
  status_ru: string;
  detail_ru: string;
  status?: string;
};

export type MoneyMonitorData = {
  title_ru: string;
  subtitle_ru: string;
  lanes: MoneyMonitorLane[];
  withdraw_alert: {
    active: boolean;
    level: string;
    title_ru: string;
    message_ru: string;
    ceo_action_ru: string;
  };
  pipeline?: { step: number; title_ru: string; detail_ru: string }[];
  model_proven: boolean;
  model_verdict_ru: string;
  toloka_role_ru?: string;
};

type Props = {
  data: MoneyMonitorData | null | undefined;
  compact?: boolean;
};

export function MoneyMonitorPanel({ data, compact }: Props) {
  if (!data) return null;

  const alert = data.withdraw_alert;
  const alertBorder =
    alert.level === "green"
      ? "border-emerald-400/50 bg-emerald-950/30"
      : alert.level === "amber"
        ? "border-amber-400/40 bg-amber-950/25"
        : "border-white/10 bg-genesis-bg/30";

  return (
    <section className={`rounded-2xl border p-5 ${alertBorder}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
          <p className="mt-1 text-sm text-genesis-muted">{data.subtitle_ru}</p>
          <p className={`mt-2 text-sm font-medium ${data.model_proven ? "text-emerald-300" : "text-amber-200"}`}>
            {data.model_verdict_ru}
          </p>
        </div>
        {!compact ? (
          <Link href="/business" className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-sm text-emerald-200 hover:bg-emerald-950/30">
            CEO Outbox →
          </Link>
        ) : null}
      </div>

      <div className={`mt-4 grid gap-3 ${compact ? "sm:grid-cols-1" : "sm:grid-cols-3"}`}>
        {data.lanes.map((lane) => (
          <div
            key={lane.id}
            className={`rounded-xl border p-4 ${
              lane.id === "b2b_client"
                ? "border-emerald-500/35 bg-emerald-950/20"
                : lane.id === "exchange_factory"
                  ? "border-sky-500/25 bg-sky-950/15"
                  : "border-white/10 bg-genesis-bg/40"
            }`}
          >
            <p className="text-lg">{lane.icon}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-genesis-muted">{lane.label_ru}</p>
            <p className="mt-2 text-lg font-semibold tabular-nums">{lane.amount_label_ru}</p>
            <p className="mt-1 text-xs text-emerald-200/80">{lane.status_ru}</p>
            <p className="mt-2 text-[11px] leading-relaxed text-genesis-muted">{lane.detail_ru}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-xl border border-white/10 bg-genesis-bg/40 p-4">
        <p className="font-medium text-white">{alert.title_ru}</p>
        <p className="mt-1 text-sm text-genesis-muted">{alert.message_ru}</p>
        <p className="mt-2 text-xs text-emerald-200/90">→ {alert.ceo_action_ru}</p>
      </div>

      {data.toloka_role_ru && !compact ? (
        <p className="mt-3 text-xs text-sky-200/70">{data.toloka_role_ru}</p>
      ) : null}

      {data.pipeline && data.pipeline.length > 0 && !compact ? (
        <ol className="mt-4 space-y-1 text-xs text-genesis-muted">
          {data.pipeline.map((p) => (
            <li key={p.step}>
              <span className="text-white/80">{p.step}. {p.title_ru}</span> — {p.detail_ru}
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
