"use client";

import type { MissionProofStep } from "./Mission2Kpi";

export type MissionProofData = {
  title_ru: string;
  subtitle_ru: string;
  progress_pct: number;
  progress_label_ru: string;
  steps: MissionProofStep[];
  next_unproven_ru: string;
};

export function MissionProofPanel({ data }: { data: MissionProofData | null | undefined }) {
  if (!data) return null;

  return (
    <section className="rounded-2xl border border-emerald-500/30 bg-emerald-950/15 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
          <p className="text-xs text-genesis-muted">{data.subtitle_ru}</p>
        </div>
        <p className="font-mono text-sm text-emerald-200">{data.progress_label_ru}</p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-emerald-500/80" style={{ width: `${data.progress_pct}%` }} />
      </div>
      <ul className="mt-4 space-y-2">
        {data.steps.map((step) => (
          <li key={step.id} className="flex items-center justify-between text-sm">
            <span className={step.done ? "text-white" : "text-genesis-muted"}>{step.label_ru}</span>
            <span>{step.icon}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-amber-200/80">Следующий не доказан: {data.next_unproven_ru}</p>
    </section>
  );
}
