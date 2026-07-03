"use client";

import Link from "next/link";

export type IncomeGoal = {
  id: string;
  label: string;
  current_label: string;
  remaining_label: string;
  progress_percent: number;
  done: boolean;
  href?: string | null;
};

export function IncomeGoalsPanel({ goals, demoMode }: { goals: IncomeGoal[]; demoMode?: boolean }) {
  if (!goals.length) return null;

  return (
    <section className="animate-fade-up overflow-hidden rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 via-genesis-panel to-genesis-panel p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="genesis-label text-emerald-400/90">Доход до цели</p>
          <p className="mt-0.5 text-sm text-genesis-muted">
            Реальные данные — без имитации дохода
            {demoMode ? " (демо)" : ""}
          </p>
        </div>
        <Link
          href="/finance"
          className="rounded-lg border border-genesis-border px-3 py-1.5 text-xs hover:border-genesis-accent"
        >
          Финансы →
        </Link>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {goals.map((goal) => (
          <GoalCard key={goal.id} goal={goal} />
        ))}
      </div>
    </section>
  );
}

function GoalCard({ goal }: { goal: IncomeGoal }) {
  const body = (
    <div
      className={`rounded-xl border p-4 transition-colors ${
        goal.done
          ? "border-emerald-500/30 bg-emerald-950/20"
          : "border-genesis-border-subtle bg-genesis-bg/40 hover:border-genesis-accent/30"
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-genesis-muted">{goal.label}</p>
      <p className="mt-2 text-2xl font-bold tabular-nums tracking-tight sm:text-xl">{goal.current_label}</p>
      <div className="my-3 h-px bg-gradient-to-r from-transparent via-genesis-border to-transparent" />
      {goal.remaining_label && (
        <p className={`text-xs ${goal.done ? "text-emerald-400" : "text-genesis-muted"}`}>
          {goal.done ? "✓ " : "осталось "}
          {goal.remaining_label}
        </p>
      )}
      {!goal.done && goal.progress_percent > 0 && (
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-genesis-border">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-genesis-accent"
            style={{ width: `${Math.min(100, goal.progress_percent)}%` }}
          />
        </div>
      )}
    </div>
  );

  if (goal.href && !goal.done) {
    return (
      <Link href={goal.href} className="block">
        {body}
      </Link>
    );
  }
  return body;
}
