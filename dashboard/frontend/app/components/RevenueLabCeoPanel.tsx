"use client";

export type CeoAction = {
  id: string;
  title_ru: string;
  action_ru: string;
  why_income_ru: string;
  env_vars?: string[];
  priority?: number;
};

export type RevenueLabBrief = {
  title_ru: string;
  headline_ru: string;
  rule_ru?: string;
  ceo_actions: CeoAction[];
};

export function RevenueLabCeoPanel({ data }: { data: RevenueLabBrief }) {
  const actions = Array.isArray(data.ceo_actions) ? data.ceo_actions : [];
  return (
    <section className="genesis-card border-amber-500/30 bg-amber-950/10 p-5 space-y-3">
      <div>
        <h2 className="text-sm font-semibold text-amber-100">{data.title_ru}</h2>
        <p className="mt-1 text-[12px] leading-relaxed text-white/85">{data.headline_ru}</p>
      </div>
      {data.rule_ru ? <p className="text-[10px] text-genesis-muted">{data.rule_ru}</p> : null}
      {!actions.length ? (
        <p className="text-xs text-emerald-200/90">Нет срочных подключений — ключи на месте или кандидаты закрыты.</p>
      ) : (
        <ul className="space-y-2">
          {actions.map((a) => (
            <li key={a.id} className="rounded-lg border border-amber-500/25 bg-black/20 px-3 py-2.5 text-xs">
              <p className="font-medium text-amber-50">{a.title_ru}</p>
              <p className="mt-1 text-white/90">→ {a.action_ru}</p>
              <p className="mt-1 text-[11px] text-genesis-muted">{a.why_income_ru}</p>
              {a.env_vars?.length ? (
                <p className="mt-1 font-mono text-[10px] text-sky-200/80">{a.env_vars.join(" · ")}</p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
