"use client";

import type { SalesFunnelData } from "./MoneyMonitorPanel";

type Props = {
  data: SalesFunnelData | null | undefined;
  compact?: boolean;
};

export function SalesFunnelPanel({ data, compact }: Props) {
  if (!data) return null;

  return (
    <section className="rounded-2xl border border-violet-500/35 bg-gradient-to-br from-violet-950/35 to-genesis-bg/50 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
          <p className="mt-1 text-sm font-medium text-violet-200/90">{data.headline_ru}</p>
          <p className="mt-1 text-xs text-genesis-muted">{data.subtitle_ru}</p>
        </div>
      </div>

      <div className={`mt-4 grid gap-2 ${compact ? "grid-cols-2 sm:grid-cols-4" : "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7"}`}>
        {data.steps.map((step) => {
          const isReceived = step.id === "received";
          const value = isReceived ? step.amount_label_ru : String(step.count ?? 0);
          return (
            <div
              key={step.id}
              className={`rounded-xl border p-3 ${
                isReceived
                  ? "border-emerald-500/45 bg-emerald-950/30 sm:col-span-2 lg:col-span-1"
                  : "border-white/10 bg-genesis-bg/40"
              }`}
            >
              <p className="text-xs text-genesis-muted">
                {step.icon} {step.label_ru}
              </p>
              <p
                className={`mt-1 tabular-nums font-bold ${
                  isReceived ? "text-2xl text-emerald-100" : compact ? "text-xl text-white" : "text-2xl text-white"
                }`}
              >
                {value}
              </p>
            </div>
          );
        })}
      </div>

      {!compact ? (
        <p className="mt-3 text-[11px] leading-relaxed text-violet-200/55">{data.training_note_ru}</p>
      ) : null}
    </section>
  );
}
