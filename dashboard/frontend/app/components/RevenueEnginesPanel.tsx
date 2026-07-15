"use client";

export type RevenueEngine = {
  id: string;
  number: number;
  label_ru: string;
  subtitle_ru: string;
  counts_as_profit: boolean;
  wallet_ru: string;
  confirmed_label_ru?: string;
  lab_journal_label_ru?: string;
};

export type RevenueEnginesData = {
  title_ru: string;
  subtitle_ru: string;
  engines: RevenueEngine[];
  money_route_ru: string;
  lab_rule_ru: string;
};

export function RevenueEnginesPanel({ data }: { data: RevenueEnginesData | null | undefined }) {
  if (!data) return null;

  return (
    <section className="rounded-2xl border border-sky-500/30 bg-sky-950/15 p-5">
      <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
      <p className="mt-1 text-xs text-genesis-muted">{data.subtitle_ru}</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {data.engines.map((e) => (
          <div
            key={e.id}
            className={`rounded-xl border p-4 ${
              e.counts_as_profit
                ? "border-emerald-500/35 bg-emerald-950/20"
                : "border-violet-500/30 bg-violet-950/15"
            }`}
          >
            <p className="text-xs uppercase tracking-wide text-genesis-muted">Двигатель {e.number}</p>
            <p className="mt-1 font-semibold text-white">{e.label_ru}</p>
            <p className="mt-1 text-xs text-genesis-muted">{e.subtitle_ru}</p>
            <p className="mt-3 text-2xl font-bold tabular-nums">
              {e.counts_as_profit ? e.confirmed_label_ru : e.lab_journal_label_ru ?? "—"}
            </p>
            <p className="mt-2 text-[11px] text-genesis-muted">{e.wallet_ru}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs leading-relaxed text-sky-200/80">{data.money_route_ru}</p>
      <p className="mt-2 text-xs leading-relaxed text-violet-200/70">{data.lab_rule_ru}</p>
    </section>
  );
}
