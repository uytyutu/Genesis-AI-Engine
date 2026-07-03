"use client";

export type CompanyOperations = {
  uptime_label: string;
  last_downtime_label: string;
  all_systems_ok: boolean;
  systems_status_label: string;
};

export function CompanyOperationsBar({ ops }: { ops?: CompanyOperations | null }) {
  if (!ops) return null;

  return (
    <section
      className={`animate-fade-up flex flex-col gap-3 rounded-2xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5 ${
        ops.all_systems_ok
          ? "border-emerald-500/25 bg-emerald-950/20"
          : "border-amber-500/25 bg-amber-950/15"
      }`}
    >
      <div>
        <p className="genesis-label text-emerald-400/90">Компания работает</p>
        <p className="mt-0.5 text-lg font-semibold tabular-nums tracking-tight">{ops.uptime_label}</p>
      </div>
      <div className="flex flex-wrap gap-6 text-sm">
        <div>
          <p className="text-xs text-genesis-muted">Последний простой</p>
          <p className="mt-0.5 font-medium tabular-nums">{ops.last_downtime_label}</p>
        </div>
        <div>
          <p className="text-xs text-genesis-muted">Все системы</p>
          <p className="mt-0.5 font-medium">{ops.systems_status_label}</p>
        </div>
      </div>
    </section>
  );
}
