import Link from "next/link";

export type RevenueStep = { id: string; label: string; done: boolean };

export type FirstRevenueJourney = {
  title: string;
  subtitle: string;
  steps: RevenueStep[];
  completed_count: number;
  total_count: number;
};

export function FirstRevenueJourneyPanel({ journey }: { journey: FirstRevenueJourney }) {
  const pct = journey.total_count
    ? Math.round((journey.completed_count / journey.total_count) * 100)
    : 0;

  return (
    <section className="animate-fade-up overflow-hidden rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-genesis-panel to-genesis-bg p-6 shadow-glow sm:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="genesis-label text-emerald-400/90">🎯 {journey.title}</p>
          <p className="mt-1 text-sm text-genesis-muted">{journey.subtitle}</p>
        </div>
        <span className="rounded-full border border-emerald-500/40 bg-emerald-950/50 px-3 py-1 text-sm font-semibold tabular-nums text-emerald-300">
          {pct}%
        </span>
      </div>

      <ul className="mt-5 space-y-2">
        {journey.steps.map((step) => (
          <li
            key={step.id}
            className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${
              step.done
                ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-100"
                : "border-genesis-border-subtle bg-genesis-bg/40"
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                step.done ? "bg-emerald-500/25 text-emerald-400" : "bg-genesis-elevated text-genesis-muted"
              }`}
            >
              {step.done ? "✓" : "○"}
            </span>
            <span className={step.done ? "line-through opacity-80" : "font-medium"}>{step.label}</span>
          </li>
        ))}
      </ul>

      <div className="mt-5 flex flex-wrap gap-3">
        <Link
          href="/create"
          className="rounded-xl bg-gradient-to-r from-emerald-600 to-genesis-accent px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90"
        >
          ➕ Создать продукт
        </Link>
        <Link
          href="/cursor"
          className="rounded-xl border border-genesis-border px-5 py-2.5 text-sm font-medium hover:border-genesis-accent/50"
        >
          📝 Связь с Cursor
        </Link>
      </div>
    </section>
  );
}
