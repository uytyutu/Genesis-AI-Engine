import Link from "next/link";
import { formatEur } from "../lib/formatEur";

export type OpportunitySnapshot = {
  engine_active: boolean;
  department_label: string;
  status_message: string;
  found_today: number;
  used_today: number;
  clients_from_opportunities: number;
  revenue_from_opportunities_eur: number;
  pending_owner_approval: number;
  prepared_count: number;
  queue_preview: {
    id?: string;
    title: string;
    status: string;
    source_id?: string;
    score?: number;
  }[];
  sources_today?: {
    source_id: string;
    label: string;
    enabled: boolean;
    count_today: number;
  }[];
  potential_value_eur?: number;
  kpi_note: string;
};

export function OpportunityEnginePanel({ snapshot }: { snapshot: OpportunitySnapshot }) {
  const sources = snapshot.sources_today?.filter((s) => s.enabled && s.count_today > 0) ?? [];

  return (
    <section className="rounded-3xl border border-violet-500/25 bg-gradient-to-br from-violet-950/30 via-genesis-panel to-genesis-bg p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="genesis-label text-violet-300/90">💼 {snapshot.department_label}</p>
          <p className="mt-1 text-sm text-genesis-muted">{snapshot.status_message}</p>
        </div>
        <Link
          href="/opportunities"
          className="rounded-full border border-violet-500/40 bg-violet-950/40 px-3 py-1 text-xs font-semibold text-violet-200 hover:bg-violet-900/50"
        >
          Открыть журнал
        </Link>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Kpi label="Найдено сегодня" value={String(snapshot.found_today)} />
        <Kpi label="В работе" value={String(snapshot.pending_owner_approval)} />
        <Kpi
          label="Потенциал"
          value={formatEur(snapshot.potential_value_eur ?? 0)}
        />
        <Kpi label="Продажи" value={String(snapshot.clients_from_opportunities)} />
      </div>

      {sources.length > 0 && (
        <ul className="mt-4 space-y-1 text-xs text-genesis-muted">
          {sources.map((s) => (
            <li key={s.source_id} className="flex justify-between">
              <span>{s.label}</span>
              <span className="tabular-nums">{s.count_today}</span>
            </li>
          ))}
        </ul>
      )}

      {snapshot.engine_active && snapshot.queue_preview.length > 0 && (
        <ul className="mt-4 space-y-2 text-sm">
          {snapshot.queue_preview.map((item) => (
            <li
              key={item.id ?? item.title}
              className="flex justify-between gap-3 rounded-lg border border-genesis-border/50 bg-genesis-bg/40 px-3 py-2"
            >
              <span>{item.title}</span>
              <span className="text-genesis-muted">
                {item.score != null ? `${item.score} · ` : ""}
                {item.status}
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-4 text-[11px] text-genesis-muted">{snapshot.kpi_note}</p>
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-3 text-center">
      <p className="text-lg font-bold tabular-nums">{value}</p>
      <p className="text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
