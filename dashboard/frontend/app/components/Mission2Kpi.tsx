"use client";

import Link from "next/link";

export type Mission2NextAction = {
  title_ru: string;
  text_ru: string;
  detail_ru: string;
  href: string;
  priority: string;
  action_id?: string;
};

type Props = {
  action: Mission2NextAction | null | undefined;
  compact?: boolean;
};

export function Mission2NextActionCard({ action, compact }: Props) {
  if (!action) return null;

  const border =
    action.priority === "high"
      ? "border-emerald-500/45 bg-emerald-950/35"
      : action.priority === "medium"
        ? "border-amber-500/35 bg-amber-950/25"
        : "border-white/10 bg-genesis-bg/40";

  return (
    <section className={`rounded-2xl border p-5 ${border}`}>
      <p className="text-xs uppercase tracking-widest text-emerald-300/80">{action.title_ru}</p>
      <p className={`mt-2 font-semibold text-white ${compact ? "text-lg" : "text-xl"}`}>{action.text_ru}</p>
      <p className="mt-2 text-sm text-genesis-muted">{action.detail_ru}</p>
      <Link
        href={action.href}
        className="mt-4 inline-flex rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
      >
        Перейти →
      </Link>
    </section>
  );
}

export type Mission2Metric = {
  id: string;
  label_ru: string;
  value: number;
  format: string;
  display?: string;
};

export function Mission2KpiTable({ metrics, title }: { metrics: Mission2Metric[]; title?: string }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-genesis-bg/30 p-5 font-mono text-sm">
      {title ? <h2 className="mb-4 font-sans text-lg font-semibold text-white">{title}</h2> : null}
      <div className="space-y-1">
        {metrics.map((m) => (
          <div key={m.id} className="flex justify-between gap-4 border-b border-white/5 py-2 last:border-0">
            <span className="text-genesis-muted">{m.label_ru}:</span>
            <span className="tabular-nums font-semibold text-white">
              {m.format === "eur" ? m.display ?? `${m.value} €` : m.value}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

export type Mission2Conversion = {
  id: string;
  label_ru: string;
  percent: number;
  from_count: number;
  to_count: number;
};

export function Mission2ConversionPanel({
  conversions,
  bottleneck,
}: {
  conversions: Mission2Conversion[];
  bottleneck?: string;
}) {
  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5">
        <h2 className="text-sm font-medium uppercase tracking-wider text-sky-200/90">Конверсия</h2>
        <ul className="mt-4 space-y-3">
          {conversions.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-3 text-sm">
              <span className="text-white/90">{c.label_ru}</span>
              <span className="tabular-nums font-bold text-sky-100">{c.percent}%</span>
            </li>
          ))}
        </ul>
      </div>
      {bottleneck ? (
        <div className="rounded-2xl border border-amber-500/25 bg-amber-950/15 p-4 text-sm text-amber-100/90">
          <p className="text-xs uppercase tracking-wider text-amber-300/80">Где тормозит</p>
          <p className="mt-2 leading-relaxed">{bottleneck}</p>
        </div>
      ) : null}
    </section>
  );
}

export type Mission2NavSection = { href: string; label_ru: string; hint_ru: string };

export function Mission2NavGrid({ sections }: { sections: Mission2NavSection[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {sections.map((s) => (
        <Link
          key={s.href}
          href={s.href}
          className="rounded-xl border border-white/10 bg-genesis-bg/40 p-4 hover:border-emerald-500/35 hover:bg-emerald-950/15"
        >
          <p className="font-medium text-white">{s.label_ru}</p>
          <p className="mt-1 text-xs text-genesis-muted">{s.hint_ru}</p>
        </Link>
      ))}
    </div>
  );
}

export type Mission2KpiData = {
  title_ru: string;
  subtitle_ru: string;
  metrics: Mission2Metric[];
  conversions: Mission2Conversion[];
  bottleneck_ru: string;
  next_action: Mission2NextAction;
  nav_sections: Mission2NavSection[];
  training_note_ru?: string;
};

export type MissionProofStep = {
  id: string;
  label_ru: string;
  done: boolean;
  icon: string;
};
