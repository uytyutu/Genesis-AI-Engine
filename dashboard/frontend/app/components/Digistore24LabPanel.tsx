"use client";

export type DigistoreCapability = {
  id: string;
  title_ru: string;
  key_present: boolean;
  status_ru: string;
  reality_chain_ru: string[];
  q1_api_allows: {
    question_ru: string;
    auth_ru?: string;
    docs_url?: string;
    answers: {
      capability: string;
      ok: boolean;
      detail_ru: string;
      api_refs?: string[];
    }[];
  };
  q2_automatable: {
    question_ru: string;
    actions: {
      id: string;
      title_ru: string;
      official: boolean;
      leads_to_first_commission: boolean | string;
      note_ru: string;
    }[];
  };
  q3_first_commission: {
    question_ru: string;
    must_happen_ru: string[];
    api_role_ru: string;
    first_euro_path: { step: number; title_ru: string; creates_money: boolean }[];
    verdict_ru: string;
  };
  next_lab_task_ru: string;
  sources_ru?: string;
};

function commissionHint(v: boolean | string): string {
  if (v === true) return "→ может дать €";
  if (v === "enables") return "→ готовит путь к €";
  return "→ само € не создаёт";
}

export function Digistore24LabPanel({ data }: { data: DigistoreCapability }) {
  return (
    <section className="genesis-card space-y-4 border-orange-500/30 bg-orange-950/10 p-5">
      <div>
        <h2 className="text-sm font-semibold text-orange-100">{data.title_ru}</h2>
        <p className="mt-1 text-[12px] text-white/85">{data.status_ru}</p>
      </div>

      <ol className="flex flex-wrap gap-1.5 text-[10px] text-orange-100/90">
        {data.reality_chain_ru.map((step, i) => (
          <li key={step} className="inline-flex items-center gap-1">
            {i > 0 ? <span className="text-genesis-muted">→</span> : null}
            <span className="rounded border border-orange-500/30 bg-black/20 px-1.5 py-0.5">{step}</span>
          </li>
        ))}
      </ol>

      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-orange-50">{data.q1_api_allows.question_ru}</h3>
        <ul className="space-y-2">
          {data.q1_api_allows.answers.map((a) => (
            <li key={a.capability} className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs">
              <p className="font-medium text-white">
                {a.ok ? "✅" : "❌"} {a.capability}
              </p>
              <p className="mt-1 text-genesis-muted">{a.detail_ru}</p>
              {a.api_refs?.length ? (
                <p className="mt-1 font-mono text-[10px] text-sky-200/80">{a.api_refs.join(" · ")}</p>
              ) : null}
            </li>
          ))}
        </ul>
        {data.q1_api_allows.auth_ru ? (
          <p className="text-[10px] text-genesis-muted">{data.q1_api_allows.auth_ru}</p>
        ) : null}
      </div>

      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-orange-50">{data.q2_automatable.question_ru}</h3>
        <ul className="space-y-2">
          {data.q2_automatable.actions.map((a) => (
            <li
              key={a.id}
              className={`rounded-lg border px-3 py-2 text-xs ${
                a.official ? "border-white/10 bg-black/20" : "border-rose-500/30 bg-rose-950/20"
              }`}
            >
              <p className="font-medium text-white">
                {a.official ? "Официально" : "Запрещено"} · {a.title_ru}
              </p>
              <p className="mt-1 text-[11px] text-amber-100/90">{commissionHint(a.leads_to_first_commission)}</p>
              <p className="mt-1 text-genesis-muted">{a.note_ru}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-orange-50">{data.q3_first_commission.question_ru}</h3>
        <p className="text-[11px] text-white/85">{data.q3_first_commission.api_role_ru}</p>
        <ul className="list-disc space-y-1 pl-4 text-[11px] text-genesis-muted">
          {data.q3_first_commission.must_happen_ru.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <ol className="space-y-1.5">
          {data.q3_first_commission.first_euro_path.map((s) => (
            <li key={s.step} className="rounded border border-white/5 bg-black/15 px-3 py-1.5 text-[11px]">
              <span className="text-orange-200">{s.step}.</span> {s.title_ru}
              <span className="ml-2 text-[10px] text-genesis-muted">
                {s.creates_money ? "€ возможно" : "ещё не €"}
              </span>
            </li>
          ))}
        </ol>
        <p className="text-[12px] font-medium text-emerald-100">{data.q3_first_commission.verdict_ru}</p>
      </div>

      <p className="rounded-lg border border-orange-500/25 bg-black/20 px-3 py-2 text-[11px] text-orange-50/90">
        {data.next_lab_task_ru}
      </p>
      {data.sources_ru ? <p className="text-[10px] text-genesis-muted">{data.sources_ru}</p> : null}
    </section>
  );
}
