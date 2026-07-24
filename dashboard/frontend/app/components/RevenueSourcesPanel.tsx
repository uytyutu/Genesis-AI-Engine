"use client";

export type RevenueSourceRow = {
  id: string;
  name: string;
  status: string;
  status_emoji: string;
  status_label: string;
  type: string;
  income_label: string;
  roi_label: string;
  confidence: string;
  automation_score: number;
  automation_label: string;
  why_ru: string;
  action_ru: string;
  scalable?: boolean;
};

export type RevenueSourcesCenter = {
  title: string;
  subtitle_ru: string;
  owner_gate_ru: string;
  discovery_ru: string;
  reality_law_ru?: string;
  law?: {
    title_ru: string;
    inequalities_ru: string[];
    trial: { note_ru: string };
  };
  sources: RevenueSourceRow[];
  summary: {
    active: number;
    candidates: number;
    blocked_or_cost: number;
    real_income_eur: number;
    verdict_ru: string;
  };
};

function statusClass(status: string): string {
  if (status === "active") return "border-emerald-500/40 bg-emerald-950/20 text-emerald-100";
  if (status === "candidate") return "border-amber-500/40 bg-amber-950/15 text-amber-100";
  if (status === "unsupported" || status === "stub") return "border-rose-500/35 bg-rose-950/15 text-rose-100";
  return "border-white/10 bg-white/5 text-genesis-muted";
}

export function RevenueSourcesPanel({ data }: { data: RevenueSourcesCenter }) {
  const rows = Array.isArray(data.sources) ? data.sources : [];
  return (
    <section className="genesis-card border-emerald-500/25 p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-white">{data.title}</h2>
        <p className="mt-1 text-[11px] text-genesis-muted">{data.subtitle_ru}</p>
      </div>
      {data.reality_law_ru ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 px-3 py-2 text-[11px] text-emerald-100">
          Закон: {data.reality_law_ru}
        </p>
      ) : null}
      {data.law?.inequalities_ru?.length ? (
        <p className="text-[10px] text-genesis-muted">{data.law.inequalities_ru.join(" · ")}</p>
      ) : null}
      <p className="text-[11px] leading-relaxed text-emerald-100/80">{data.owner_gate_ru}</p>
      <p className="text-[11px] text-genesis-muted">{data.discovery_ru}</p>
      {data.law?.trial?.note_ru ? (
        <p className="text-[10px] text-amber-100/80">{data.law.trial.note_ru}</p>
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-white/10 text-[10px] uppercase tracking-wide text-genesis-muted">
              <th className="py-2 pr-3 font-medium">Источник</th>
              <th className="py-2 pr-3 font-medium">Статус</th>
              <th className="py-2 pr-3 font-medium">Тип</th>
              <th className="py-2 pr-3 font-medium">Доход</th>
              <th className="py-2 pr-3 font-medium">ROI</th>
              <th className="py-2 pr-3 font-medium">Confidence</th>
              <th className="py-2 pr-3 font-medium">Automation</th>
              <th className="py-2 font-medium">Действие</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id} className="border-b border-white/5 align-top">
                <td className="py-2.5 pr-3">
                  <p className="font-medium text-white">{s.name}</p>
                  <p className="mt-1 max-w-xs text-[10px] leading-snug text-genesis-muted">{s.why_ru}</p>
                </td>
                <td className="py-2.5 pr-3">
                  <span className={`inline-flex rounded border px-2 py-0.5 text-[10px] ${statusClass(s.status)}`}>
                    {s.status_emoji} {s.status_label}
                  </span>
                </td>
                <td className="py-2.5 pr-3 text-white/80">{s.type}</td>
                <td className="py-2.5 pr-3 text-white">{s.income_label}</td>
                <td className="py-2.5 pr-3 text-white/80">{s.roi_label}</td>
                <td className="py-2.5 pr-3 font-mono text-[10px] text-violet-200">{s.confidence}</td>
                <td className="py-2.5 pr-3 text-sky-200">{s.automation_label}</td>
                <td className="py-2.5 text-genesis-muted">{s.action_ru}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[11px] leading-relaxed text-white/70">{data.summary.verdict_ru}</p>
      <p className="text-[10px] text-genesis-muted">
        Active {data.summary.active} · Candidate {data.summary.candidates} · Blocked/cost{" "}
        {data.summary.blocked_or_cost} · Real {data.summary.real_income_eur.toFixed(2)} €
      </p>
    </section>
  );
}
