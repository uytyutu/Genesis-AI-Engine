"use client";

export type CompanyReadinessItem = {
  id: string;
  label: string;
  done: boolean;
};

export type CompanyReadiness = {
  percent: number;
  completed_count: number;
  total_count: number;
  items: CompanyReadinessItem[];
  remaining_labels: string[];
};

export function CompanyReadinessPanel({
  readiness,
  demoMode,
}: {
  readiness?: CompanyReadiness | null;
  demoMode?: boolean;
}) {
  if (!readiness) return null;

  const filled = Math.round(readiness.percent / 10);
  const bar = "█".repeat(filled) + "░".repeat(10 - filled);
  const remaining = readiness.items.filter((i) => !i.done);

  return (
    <section className="animate-fade-up overflow-hidden rounded-2xl border border-indigo-500/25 bg-gradient-to-br from-indigo-950/35 via-genesis-panel to-genesis-panel p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="genesis-label text-indigo-300/90">Готовность компании</p>
          <p className="mt-0.5 text-sm text-genesis-muted">
            Реальные этапы до первого платежа{demoMode ? " (демо)" : ""}
          </p>
        </div>
        <p className="text-3xl font-bold tabular-nums tracking-tight text-indigo-200">{readiness.percent}%</p>
      </div>

      <p className="mt-4 font-mono text-sm tracking-widest text-indigo-300/80">{bar}</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="genesis-label mb-2">Этапы</p>
          <ul className="space-y-1.5 text-sm">
            {readiness.items.map((item) => (
              <li
                key={item.id}
                className={item.done ? "text-emerald-400/90" : "text-genesis-muted"}
              >
                {item.done ? "✔" : "○"} {item.label}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="genesis-label mb-2">Что осталось</p>
          {remaining.length === 0 ? (
            <p className="text-sm text-emerald-400">Всё готово — фокус на первом платеже</p>
          ) : (
            <ul className="space-y-1.5 text-sm text-genesis-muted">
              {remaining.map((item) => (
                <li key={item.id}>○ {item.label}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
