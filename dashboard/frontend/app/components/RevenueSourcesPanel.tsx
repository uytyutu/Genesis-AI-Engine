"use client";

import { useState } from "react";

export type RevenueSourceRow = {
  id: string;
  name: string;
  status: string;
  status_emoji: string;
  status_label: string;
  keys_present?: boolean;
  type: string;
  income_label: string;
  roi_label: string;
  confidence: string;
  automation_score: number;
  automation_label: string;
  why_ru: string;
  action_ru: string;
  scalable?: boolean;
  stage?: string;
  why_not_earned_ru?: string;
  next_step_ru?: string;
  pipeline_steps?: Array<{ id?: string; label?: string; done?: boolean }>;
  why_button_label_ru?: string;
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
  keys_probe?: {
    stripe_secret?: boolean;
    stripe_webhook?: boolean;
    awin?: boolean;
    digistore24?: boolean;
    env_file_ru?: string;
    note_ru?: string;
  };
  sources: RevenueSourceRow[];
  summary: {
    active: number;
    candidates: number;
    blocked_or_cost: number;
    real_income_eur: number;
    keys_present?: number;
    verdict_ru: string;
  };
};

function statusClass(status: string, keysPresent?: boolean): string {
  if (status === "active") return "border-emerald-500/40 bg-emerald-950/20 text-emerald-100";
  if (keysPresent) return "border-sky-500/40 bg-sky-950/20 text-sky-100";
  if (status === "candidate") return "border-amber-500/40 bg-amber-950/15 text-amber-100";
  if (status === "unsupported" || status === "stub") return "border-rose-500/35 bg-rose-950/15 text-rose-100";
  return "border-white/10 bg-white/5 text-genesis-muted";
}

function SourceWhy({ s }: { s: RevenueSourceRow }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-1.5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded border border-amber-400/30 bg-amber-950/20 px-2 py-0.5 text-[10px] text-amber-100 hover:bg-amber-950/40"
      >
        {open ? "Скрыть" : s.why_button_label_ru || "Почему не заработало?"}
      </button>
      {open ? (
        <div className="mt-2 space-y-1.5 rounded-lg border border-white/10 bg-black/30 px-2.5 py-2 text-[10px] leading-snug text-zinc-300">
          <p>
            <span className="text-zinc-500">Этап: </span>
            <span className="font-medium text-white">{s.stage || s.status}</span>
          </p>
          <p>
            <span className="text-zinc-500">Почему? </span>
            {s.why_not_earned_ru || s.why_ru}
          </p>
          <p>
            <span className="text-zinc-500">Следующее действие: </span>
            <span className="text-emerald-200">{s.next_step_ru || s.action_ru}</span>
          </p>
          {(s.pipeline_steps || []).length > 0 ? (
            <ul className="mt-1 space-y-0.5 font-mono text-[9px] text-zinc-400">
              {(s.pipeline_steps || []).map((p) => (
                <li key={p.id || p.label}>
                  {p.done ? "✓" : "○"} {p.label}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
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

      {data.keys_probe ? (
        <div className="rounded-lg border border-sky-500/25 bg-sky-950/20 px-3 py-2 text-[11px] text-sky-100/90 space-y-1">
          <p className="font-medium text-sky-50">Что backend видит в env (да/нет, без секретов)</p>
          <p>
            Stripe secret: {data.keys_probe.stripe_secret ? "✅" : "❌"}
            {" · "}
            Stripe webhook: {data.keys_probe.stripe_webhook ? "✅" : "❌"}
            {" · "}
            Digistore24: {data.keys_probe.digistore24 ? "✅" : "❌"}
            {" · "}
            Awin: {data.keys_probe.awin ? "✅" : "❌"}
          </p>
          {data.keys_probe.env_file_ru ? (
            <p className="text-genesis-muted">Файл: {data.keys_probe.env_file_ru}</p>
          ) : null}
          {data.keys_probe.note_ru ? (
            <p className="text-genesis-muted">{data.keys_probe.note_ru}</p>
          ) : null}
        </div>
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
                  <p className="mt-0.5 font-mono text-[9px] text-zinc-500">{s.stage}</p>
                  <SourceWhy s={s} />
                </td>
                <td className="py-2.5 pr-3">
                  <span
                    className={`inline-flex rounded border px-2 py-0.5 text-[10px] ${statusClass(
                      s.status,
                      s.keys_present,
                    )}`}
                  >
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
        Active {data.summary.active} · Candidate {data.summary.candidates} · Keys seen{" "}
        {data.summary.keys_present ?? 0} · Blocked/cost {data.summary.blocked_or_cost} · Real{" "}
        {data.summary.real_income_eur.toFixed(2)} €
      </p>
    </section>
  );
}
