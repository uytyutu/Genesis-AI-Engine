"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { publicApiBase } from "../lib/publicApiBase";
import { logCommerceEvent } from "../lib/commerceFunnel";

type CheckRow = {
  id: string;
  label: string;
  status: "pass" | "fail" | "unavailable";
  detail: string;
};

type Recommendation = {
  id: string;
  title: string;
  price_label: string;
  summary: string;
  availability: string;
  cta: string;
  cta_href?: string | null;
  cta_label: string;
  recommended?: boolean;
  why?: string;
  package_id?: string | null;
  alt_ctas?: Array<{ href: string; label: string }>;
};

type AnalysisReport = {
  health_score: number;
  url: string;
  final_url?: string;
  title?: string;
  strengths: string[];
  problems: string[];
  checks: CheckRow[];
  recommendations: Recommendation[];
  justification: string;
  vector_plain?: string;
  case_id?: string;
  repair_quote?: {
    package_id?: string | null;
    price_eur?: number | null;
    label?: string | null;
    prefer_new?: boolean;
  };
  error?: string | null;
  principle?: string;
};

/**
 * Website Analysis — free funnel entry on /site.
 * Recommend Repair or New Website; Repair is not a separate hero card.
 */
export function WebsiteAnalysisPanel({
  market,
  onAskVector,
}: {
  market: string;
  onAskVector: () => void;
}) {
  const { t, i18n } = useTranslation("site");
  const [url, setUrl] = useState("https://");
  const [email, setEmail] = useState("");
  const [problemNote, setProblemNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<AnalysisReport | null>(null);

  function orderHref(href: string, caseId?: string) {
    const base = `${href}${href.includes("?") ? "&" : "?"}market=${encodeURIComponent(market)}`;
    if (!caseId) return base;
    return `${base}&analysis_case=${encodeURIComponent(caseId)}`;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const locale = (i18n.language || "de").slice(0, 2);
    try {
      const res = await fetch(`${publicApiBase()}/api/public/website-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          email: email.trim(),
          problem_note: problemNote.trim(),
          locale,
          use_cache: false,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(String(body.detail || "analysis_failed"));
        setReport(null);
        return;
      }
      setReport(body as AnalysisReport);
      logCommerceEvent("tier_page_view", null, "website_analysis", {
        niche: null,
      });
    } catch {
      setError(t("analysis.apiError"));
      setReport(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 sm:p-6">
      <h3 className="text-lg font-semibold text-white">{t("analysis.title")}</h3>
      <p className="mt-2 text-sm text-zinc-400">{t("analysis.intro")}</p>

      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://company.de"
          className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-sm text-white placeholder:text-zinc-600"
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t("analysis.emailPh")}
          className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-sm text-white placeholder:text-zinc-600"
        />
        <textarea
          value={problemNote}
          onChange={(e) => setProblemNote(e.target.value)}
          placeholder={t("analysis.notePh")}
          rows={2}
          className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-sm text-white placeholder:text-zinc-600"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
        >
          {busy ? t("analysis.submitting") : t("analysis.submit")}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}

      {report ? (
        <div className="mt-6 space-y-5 border-t border-white/10 pt-5">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-zinc-500">
                {t("analysis.scoreLabel")}
              </p>
              <p className="text-4xl font-semibold text-white">
                {report.health_score}
                <span className="text-lg text-zinc-500"> / 100</span>
              </p>
            </div>
            <div className="min-w-0 flex-1 text-sm text-zinc-400">
              <p className="truncate text-zinc-300">{report.final_url || report.url}</p>
              {report.title ? (
                <p className="truncate text-xs text-zinc-500">{report.title}</p>
              ) : null}
              {report.case_id ? (
                <p className="mt-1 text-xs text-sky-300/80">
                  {t("analysis.caseLabel", { id: report.case_id })}
                </p>
              ) : null}
            </div>
          </div>

          {report.vector_plain ? (
            <div className="rounded-xl border border-sky-400/20 bg-sky-950/20 p-4">
              <p className="text-sm font-medium text-sky-100">{t("analysis.vectorPlain")}</p>
              <p className="mt-2 text-sm text-zinc-300 whitespace-pre-wrap">
                {report.vector_plain}
              </p>
            </div>
          ) : null}

          {report.strengths?.length ? (
            <div>
              <p className="text-sm font-medium text-emerald-200">{t("analysis.strengths")}</p>
              <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                {report.strengths.map((s) => (
                  <li key={s}>✓ {s}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {report.problems?.length ? (
            <div>
              <p className="text-sm font-medium text-amber-200">{t("analysis.problems")}</p>
              <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                {report.problems.map((p) => (
                  <li key={p}>⚠ {p}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div>
            <p className="text-sm font-medium text-zinc-200">{t("analysis.checks")}</p>
            <ul className="mt-2 space-y-2">
              {(report.checks || []).map((c) => (
                <li
                  key={c.id}
                  className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm"
                >
                  <span
                    className={
                      c.status === "pass"
                        ? "text-emerald-300"
                        : c.status === "fail"
                          ? "text-amber-200"
                          : "text-zinc-500"
                    }
                  >
                    {c.status === "pass" ? "✓" : c.status === "fail" ? "⚠" : "○"}{" "}
                    {c.label}
                  </span>
                  <p className="mt-0.5 text-xs text-zinc-500">{c.detail}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-sm font-medium text-zinc-100">{t("analysis.why")}</p>
            <p className="mt-2 text-sm text-zinc-300 whitespace-pre-wrap">
              {report.justification}
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium text-white">{t("analysis.next")}</p>
            {(report.recommendations || []).map((r) => (
              <div
                key={r.id}
                className={`rounded-xl border p-4 ${
                  r.recommended
                    ? "border-emerald-500/40 bg-emerald-950/20"
                    : "border-white/10 bg-black/20"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium text-white">
                    {r.title}
                    {r.recommended ? (
                      <span className="ml-2 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                        {t("analysis.recommended")}
                      </span>
                    ) : null}
                  </p>
                  <p className="text-sm text-emerald-200">{r.price_label}</p>
                </div>
                <p className="mt-1 text-sm text-zinc-400">{r.summary}</p>
                {r.why ? (
                  <p className="mt-2 text-xs text-emerald-100/80">{r.why}</p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  {r.cta === "order_now" && r.cta_href ? (
                    <Link
                      href={orderHref(r.cta_href, report.case_id)}
                      onClick={() =>
                        logCommerceEvent(
                          "tier_select",
                          r.package_id || r.id,
                          "website_analysis",
                        )
                      }
                      className="inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
                    >
                      {r.cta_label}
                    </Link>
                  ) : (
                    <span className="inline-flex rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-1.5 text-xs font-semibold text-amber-100/90">
                      {r.cta_label}
                    </span>
                  )}
                  {(r.alt_ctas || []).map((a) => (
                    <Link
                      key={a.href}
                      href={orderHref(a.href, report.case_id)}
                      className="inline-flex rounded-xl border border-white/20 px-3 py-2 text-xs font-medium text-white hover:bg-white/5"
                    >
                      {a.label}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={onAskVector}
            className="text-sm font-medium text-sky-300 hover:underline"
          >
            {t("analysis.askVector")}
          </button>
        </div>
      ) : null}
    </article>
  );
}
