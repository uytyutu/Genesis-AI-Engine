"use client";

import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

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

const fieldClass =
  "w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none transition focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/20";

export function BusinessInterviewPanel({ value, onChange, onParsed }: Props) {
  const { t, i18n } = useTranslation("site");
  const lang = (i18n.language || "de").slice(0, 2);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{
    subniche?: string;
    scale?: string;
    components?: { label: string; why: string }[];
    technical?: Record<string, unknown>;
    law?: string;
  } | null>(null);
  const [questions, setQuestions] = useState<ClarifyQ[]>([]);
  const [dreamPromptOverride, setDreamPromptOverride] = useState("");
  const [err, setErr] = useState("");
  const dreamPrompt =
    dreamPromptOverride.trim() || t("order.interview.dreamPromptDefault");

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
      if (data.dream_prompt_de) setDreamPromptOverride(String(data.dream_prompt_de));
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
      setErr(e instanceof Error ? e.message : t("order.interview.parseFail"));
    } finally {
      setBusy(false);
    }
  };

  const clarifyPrompt = (q: ClarifyQ) =>
    lang === "de" ? q.prompt_de || q.prompt : q.prompt;
  const clarifyOption = (o: ClarifyQ["options"][number]) =>
    lang === "de" ? o.label_de || o.label : o.label;

  return (
    <section
      className="relative overflow-hidden rounded-3xl border border-emerald-400/25 bg-gradient-to-br from-emerald-950/40 via-[#0c1220]/90 to-violet-950/30 p-5 shadow-[0_0_48px_-18px_rgba(16,185,129,0.45)] sm:p-6"
      data-virtus-interview="1"
    >
      <div
        className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-emerald-400/10 blur-3xl"
        aria-hidden
      />
      <header className="relative space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/35 bg-emerald-500/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-300" aria-hidden />
            {t("order.interview.badge")}
          </span>
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">
          {t("order.interview.title")}
        </h2>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-300">
          {t("order.interview.subtitle")}
        </p>
      </header>

      <div className="relative mt-5 space-y-5">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-zinc-100">
            {t("order.interview.talkLabel")}
          </span>
          <textarea
            className={`${fieldClass} min-h-[120px]`}
            placeholder={t("order.interview.talkPh")}
            value={value.dialogue}
            onChange={(e) => patch({ dialogue: e.target.value })}
          />
        </label>
        <button
          type="button"
          disabled={busy || !value.dialogue.trim()}
          onClick={() => void runParse()}
          className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black shadow-[0_0_28px_-8px_rgba(16,185,129,0.8)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy ? t("order.interview.understanding") : t("order.interview.understandCta")}
        </button>
        {err ? (
          <p className="text-sm text-rose-300" role="alert">
            {err}
          </p>
        ) : null}

        {questions.length > 0 ? (
          <div className="space-y-4 rounded-2xl border border-amber-400/30 bg-amber-950/25 p-4">
            <p className="text-sm font-semibold text-amber-50">
              {t("order.interview.clarifyTitle")}
            </p>
            <p className="text-xs text-amber-100/75">{t("order.interview.clarifyHint")}</p>
            {questions.map((q) => (
              <div key={q.id} className="space-y-2">
                <p className="text-sm font-medium text-white">{clarifyPrompt(q)}</p>
                {q.why ? <p className="text-xs text-zinc-400">{q.why}</p> : null}
                <div className="flex flex-wrap gap-2">
                  {q.options.map((o) => {
                    const active = value.clarify_answers[q.id] === o.id;
                    return (
                      <button
                        key={o.id}
                        type="button"
                        onClick={() => answerClarify(q.id, o.id)}
                        className={`rounded-full border px-3 py-1.5 text-xs transition ${
                          active
                            ? "border-emerald-400/60 bg-emerald-500/20 text-emerald-50"
                            : "border-white/15 bg-black/30 text-zinc-200 hover:border-white/30"
                        }`}
                      >
                        {clarifyOption(o)}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <details className="group rounded-2xl border border-white/10 bg-black/25 open:border-violet-400/30">
          <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-zinc-100 marker:content-none [&::-webkit-details-marker]:hidden">
            <span className="flex items-center justify-between gap-2">
              {t("order.interview.dreamLabel")}
              <span className="text-xs text-zinc-500 group-open:hidden">+</span>
              <span className="hidden text-xs text-zinc-500 group-open:inline">−</span>
            </span>
          </summary>
          <div className="space-y-2 border-t border-white/10 px-4 pb-4 pt-3">
            <p className="text-xs text-zinc-400">{dreamPrompt}</p>
            <textarea
              className={`${fieldClass} min-h-[72px]`}
              placeholder={t("order.interview.dreamPh")}
              value={value.dream_vision}
              onChange={(e) => patch({ dream_vision: e.target.value })}
              onBlur={() => {
                if (value.dream_vision.trim()) void runParse();
              }}
            />
          </div>
        </details>

        {preview?.subniche ? (
          <div className="space-y-2 rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-sm text-zinc-200">
            <p>
              <strong className="text-white">{t("order.interview.subniche")}:</strong>{" "}
              {preview.subniche}
              {preview.scale ? (
                <>
                  {" "}
                  · <strong className="text-white">{t("order.interview.scale")}:</strong>{" "}
                  {preview.scale}
                </>
              ) : null}
            </p>
            {preview.components?.length ? (
              <ul className="space-y-1 text-xs text-zinc-300">
                {preview.components.slice(0, 8).map((c) => (
                  <li key={c.label}>
                    ✓ {c.label} — <span className="text-zinc-500">{c.why}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium text-zinc-100">{t("order.interview.companyName")}</span>
            <input
              className={fieldClass}
              value={value.company_name}
              onChange={(e) => patch({ company_name: e.target.value })}
              placeholder={t("order.interview.companyNamePh")}
            />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium text-zinc-100">{t("order.interview.city")}</span>
            <input
              className={fieldClass}
              value={value.city}
              onChange={(e) => patch({ city: e.target.value })}
              placeholder={t("order.interview.cityPh")}
            />
          </label>
        </div>

        <label className="block space-y-1.5 text-sm">
          <span className="font-medium text-zinc-100">{t("order.interview.whyChoose")}</span>
          <textarea
            className={`${fieldClass} min-h-[72px]`}
            value={value.differentiator}
            onChange={(e) => patch({ differentiator: e.target.value })}
            placeholder={t("order.interview.whyChoosePh")}
          />
        </label>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-zinc-100">
            {t("order.interview.feelLabel")}
          </legend>
          <div className="flex flex-wrap gap-2">
            {STYLES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => patch({ style: s })}
                className={`rounded-full border px-3 py-1.5 text-xs transition ${
                  value.style === s
                    ? "border-emerald-400/50 bg-emerald-500/20 text-emerald-50"
                    : "border-white/15 bg-black/30 text-zinc-300 hover:border-white/30"
                }`}
              >
                {t(`order.interview.style.${s}`, { defaultValue: s })}
              </button>
            ))}
          </div>
        </fieldset>

        <label className="block space-y-1.5 text-sm">
          <span className="font-medium text-zinc-100">{t("order.interview.topServices")}</span>
          <input
            className={fieldClass}
            value={value.top_services}
            onChange={(e) => patch({ top_services: e.target.value })}
            placeholder={t("order.interview.topServicesPh")}
          />
        </label>
      </div>
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
