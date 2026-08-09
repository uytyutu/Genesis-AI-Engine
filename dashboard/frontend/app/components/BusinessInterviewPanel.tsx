"use client";

import { useCallback, useState } from "react";

export type InterviewState = {
  dialogue: string;
  company_name: string;
  about: string;
  city: string;
  clients_who: string;
  style: string;
  site_jobs: string[];
  differentiator: string;
  top_services: string;
  wishes: string;
  niche: string;
  clarify_answers: Record<string, string>;
  dream_vision: string;
  business_scale: string;
};

type ClarifyQ = {
  id: string;
  prompt: string;
  prompt_de?: string;
  why?: string;
  options: { id: string; label: string; label_de?: string }[];
};

const STYLES = [
  "modern",
  "premium",
  "minimal",
  "friendly",
  "strict",
  "technological",
  "luxury",
  "natural",
  "german_classic",
  "youthful",
] as const;

type Props = {
  value: InterviewState;
  onChange: (next: InterviewState) => void;
  onParsed?: (preview: {
    interview: Record<string, unknown>;
    intelligence: Record<string, unknown>;
    recommended_components: { id: string; label: string; why: string }[];
    clarifying_questions?: ClarifyQ[];
  }) => void;
};

export function emptyInterview(partial?: Partial<InterviewState>): InterviewState {
  return {
    dialogue: "",
    company_name: "",
    about: "",
    city: "",
    clients_who: "",
    style: "modern",
    site_jobs: ["leads", "services"],
    differentiator: "",
    top_services: "",
    wishes: "",
    niche: "",
    clarify_answers: {},
    dream_vision: "",
    business_scale: "",
    ...partial,
  };
}

export function BusinessInterviewPanel({ value, onChange, onParsed }: Props) {
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{
    subniche?: string;
    scale?: string;
    components?: { label: string; why: string }[];
    technical?: Record<string, unknown>;
    law?: string;
  } | null>(null);
  const [questions, setQuestions] = useState<ClarifyQ[]>([]);
  const [dreamPrompt, setDreamPrompt] = useState(
    "Wenn Budget egal wäre — wie soll Ihre Firma in fünf Jahren aussehen?",
  );
  const [err, setErr] = useState("");

  const patch = useCallback(
    (p: Partial<InterviewState>) => onChange({ ...value, ...p }),
    [onChange, value],
  );

  const answerClarify = (qid: string, oid: string) => {
    const nextAnswers = { ...value.clarify_answers, [qid]: oid };
    const next = {
      ...value,
      clarify_answers: nextAnswers,
      business_scale: qid === "business_scale" ? oid : value.business_scale,
    };
    onChange(next);
    void runParse(next);
  };

  const runParse = async (state: InterviewState = value) => {
    setBusy(true);
    setErr("");
    try {
      const res = await fetch("/api/public/business-interview/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          free_text: state.dialogue,
          company_name: state.company_name,
          city: state.city,
          style: state.style,
          site_jobs: state.site_jobs,
          differentiator: state.differentiator,
          top_services: state.top_services,
          wishes: state.wishes,
          niche: state.niche,
          about: state.about,
          clients_who: state.clients_who,
          clarify_answers: state.clarify_answers,
          dream_vision: state.dream_vision,
          business_scale: state.business_scale,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const iv = data.interview || {};
      patch({
        company_name: state.company_name || String(iv.company_name || ""),
        city: state.city || String(iv.city || ""),
        about: state.about || String(iv.about || ""),
        style: state.style || String(iv.style || "modern"),
        differentiator: state.differentiator || String(iv.differentiator || ""),
        niche: state.niche || String(iv.niche_hint || ""),
        site_jobs: state.site_jobs.length
          ? state.site_jobs
          : Array.isArray(iv.site_jobs)
            ? iv.site_jobs.map(String)
            : state.site_jobs,
        wishes: state.wishes || String(iv.wishes || ""),
        clients_who: state.clients_who || String(iv.clients_who || ""),
        business_scale: state.business_scale || String(iv.business_scale || ""),
        dream_vision: state.dream_vision || String(iv.dream_vision || ""),
      });
      const comps = Array.isArray(data.recommended_components)
        ? data.recommended_components
        : [];
      const qs = Array.isArray(data.clarifying_questions) ? data.clarifying_questions : [];
      setQuestions(qs);
      if (data.dream_prompt_de) setDreamPrompt(String(data.dream_prompt_de));
      setPreview({
        subniche: String(data.intelligence?.subniche_label || ""),
        scale: String(data.intelligence?.business_scale || ""),
        components: comps.map((c: { label: string; why: string }) => ({
          label: c.label,
          why: c.why,
        })),
        technical: data.technical_decisions || {},
        law: String(data.law || ""),
      });
      onParsed?.(data);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Parse failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm space-y-5">
      <header>
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">
          Smart AI Business Interview
        </p>
        <h2 className="mt-1 text-xl font-semibold text-zinc-900">
          Tell us about your business — we design the digital solution
        </h2>
        <p className="mt-1 text-sm text-zinc-600">
          No templates. No sticky-header checkboxes. Virtus asks about the business, then decides
          architecture itself.
        </p>
      </header>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-zinc-800">Talk to Virtus</span>
        <textarea
          className="w-full min-h-[120px] rounded-xl border border-zinc-300 px-3 py-2 text-sm"
          placeholder="Example: Ich bin Psychologe in Berlin — arbeite vor allem online mit Angstpatienten. Will Vertrauen und Ruhe, nicht Klinik-Kälte."
          value={value.dialogue}
          onChange={(e) => patch({ dialogue: e.target.value })}
        />
      </label>
      <button
        type="button"
        disabled={busy || !value.dialogue.trim()}
        onClick={() => void runParse()}
        className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
      >
        {busy ? "Understanding…" : "Understand my business"}
      </button>
      {err ? <p className="text-sm text-red-600">{err}</p> : null}

      {questions.length > 0 ? (
        <div className="space-y-4 rounded-xl border border-amber-200 bg-amber-50/60 p-4">
          <p className="text-sm font-semibold text-amber-950">Clarifying questions</p>
          <p className="text-xs text-amber-900/80">
            These change the product — not the template skin.
          </p>
          {questions.map((q) => (
            <div key={q.id} className="space-y-2">
              <p className="text-sm font-medium text-zinc-900">
                {q.prompt_de || q.prompt}
              </p>
              {q.why ? <p className="text-xs text-zinc-500">{q.why}</p> : null}
              <div className="flex flex-wrap gap-2">
                {q.options.map((o) => {
                  const active = value.clarify_answers[q.id] === o.id;
                  return (
                    <button
                      key={o.id}
                      type="button"
                      onClick={() => answerClarify(q.id, o.id)}
                      className={`rounded-full border px-3 py-1.5 text-xs ${
                        active
                          ? "border-amber-800 bg-amber-900 text-white"
                          : "border-amber-300 bg-white text-amber-950"
                      }`}
                    >
                      {o.label_de || o.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-zinc-800">Dream Mode</span>
        <p className="text-xs text-zinc-500">{dreamPrompt}</p>
        <textarea
          className="w-full min-h-[72px] rounded-xl border border-zinc-300 px-3 py-2 text-sm"
          placeholder="Beispiel: Die beste Dachreinigung Berlins werden — Referenz für Qualität."
          value={value.dream_vision}
          onChange={(e) => patch({ dream_vision: e.target.value })}
          onBlur={() => {
            if (value.dream_vision.trim()) void runParse();
          }}
        />
      </label>

      {preview?.subniche ? (
        <div className="rounded-xl bg-zinc-50 p-3 text-sm text-zinc-700 space-y-2">
          <p>
            <strong>Sub-niche:</strong> {preview.subniche}
            {preview.scale ? (
              <>
                {" "}
                · <strong>Scale:</strong> {preview.scale}
              </>
            ) : null}
          </p>
          {preview.components?.length ? (
            <ul className="space-y-1">
              {preview.components.slice(0, 8).map((c) => (
                <li key={c.label}>
                  ✓ {c.label} — <span className="text-zinc-500">{c.why}</span>
                </li>
              ))}
            </ul>
          ) : null}
          {preview.technical?.page_architecture ? (
            <p className="text-xs text-zinc-500 border-t border-zinc-200 pt-2">
              Factory decided: {String(preview.technical.page_architecture)} · CTA{" "}
              {String(preview.technical.primary_cta)} — you did not pick this.
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Company name</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={value.company_name}
            onChange={(e) => patch({ company_name: e.target.value })}
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">City</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={value.city}
            onChange={(e) => patch({ city: e.target.value })}
          />
        </label>
      </div>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Why should clients choose you?</span>
        <textarea
          className="w-full min-h-[72px] rounded-lg border border-zinc-300 px-3 py-2"
          value={value.differentiator}
          onChange={(e) => patch({ differentiator: e.target.value })}
          placeholder="This becomes the Hero seed."
        />
      </label>

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">How should you feel?</legend>
        <div className="flex flex-wrap gap-2">
          {STYLES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => patch({ style: s })}
              className={`rounded-full border px-3 py-1 text-xs ${
                value.style === s
                  ? "border-zinc-900 bg-zinc-900 text-white"
                  : "border-zinc-300 text-zinc-700"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Top services (comma-separated)</span>
        <input
          className="w-full rounded-lg border border-zinc-300 px-3 py-2"
          value={value.top_services}
          onChange={(e) => patch({ top_services: e.target.value })}
        />
      </label>
    </section>
  );
}

export function interviewOrderFields(value: InterviewState): Record<string, unknown> {
  return {
    dialogue: value.dialogue,
    business_interview: {
      company_name: value.company_name,
      about: value.about,
      city: value.city,
      clients_who: value.clients_who,
      style: value.style,
      site_jobs: value.site_jobs,
      differentiator: value.differentiator,
      top_services: value.top_services
        .split(/[,;\n]/)
        .map((s) => s.trim())
        .filter(Boolean),
      wishes: value.wishes,
      niche: value.niche,
      free_text: value.dialogue,
      clarify_answers: value.clarify_answers,
      dream_vision: value.dream_vision,
      business_scale: value.business_scale,
    },
    why_choose_us: value.differentiator,
    who_is_company: value.about || value.dialogue,
    clients_who: value.clients_who,
    site_jobs: value.site_jobs,
    wishes: value.wishes,
    dream_vision: value.dream_vision,
    clarify_answers: value.clarify_answers,
    business_scale: value.business_scale,
    brand_style: value.style,
    niche: value.niche || undefined,
    city: value.city || undefined,
    business_name: value.company_name || undefined,
    services_list: value.top_services
      .split(/[,;\n]/)
      .map((s) => s.trim())
      .filter(Boolean),
  };
}
