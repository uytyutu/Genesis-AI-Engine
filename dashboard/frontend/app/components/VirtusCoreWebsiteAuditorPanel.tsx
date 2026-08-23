"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Finding = {
  id: string;
  category: string;
  severity: string;
  message: string;
  action?: { kind?: string; label?: string; coming?: string; href?: string };
};

type AuditorReport = {
  ok: boolean;
  product?: string;
  report_id?: string;
  overall_business_score?: number;
  website?: Record<string, number>;
  germany_legal?: Record<string, { label: string; pass: boolean }>;
  business?: Record<string, { label: string; pass: boolean }>;
  findings?: Finding[];
  ai_summary?: string;
  error?: string;
  branding?: { name?: string; tagline?: string };
};

function ScoreBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="font-medium text-zinc-200">{label}</span>
        <span className="tabular-nums text-zinc-400">{value}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-400 to-emerald-400"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}

export function VirtusCoreWebsiteAuditorPanel({
  locale = "de",
}: {
  locale?: string;
}) {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AuditorReport | null>(null);

  const exportBase = useMemo(() => {
    if (!report?.report_id) return null;
    return `${API}/api/public/vc-auditor/${report.report_id}/export`;
  }, [report?.report_id]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/public/vc-auditor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), locale }),
      });
      const body = (await res.json()) as AuditorReport;
      if (!res.ok || body.ok === false) {
        throw new Error(body.error || "audit_failed");
      }
      setReport(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-300/80">
          Virtus Core
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Virtus Core Website Auditor
        </h1>
        <p className="max-w-2xl text-sm text-zinc-400">
          {report?.branding?.tagline ||
            "What exactly should I fix to make my website better?"}
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 sm:p-6"
      >
        <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Website URL
        </label>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://company.de"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white outline-none ring-emerald-500/40 focus:ring"
            required
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
          >
            {busy ? "Analysiere…" : "Audit starten"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      </form>

      {report?.ok ? (
        <div className="space-y-5">
          <section className="rounded-3xl border border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-transparent p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300/80">
              Overall Business Score
            </p>
            <p className="mt-2 text-5xl font-semibold tabular-nums tracking-tight">
              {report.overall_business_score}
              <span className="text-2xl opacity-50"> / 100</span>
            </p>
            <p className="mt-3 text-sm leading-relaxed text-zinc-300">
              {report.ai_summary}
            </p>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
              <h2 className="text-sm font-semibold text-white">Website</h2>
              {Object.entries(report.website || {}).map(([k, v]) => (
                <ScoreBar key={k} label={k.toUpperCase()} value={v} />
              ))}
            </div>
            <div className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <h2 className="text-sm font-semibold text-white">Germany Legal</h2>
                <ul className="mt-3 space-y-1.5 text-sm">
                  {Object.values(report.germany_legal || {}).map((row) => (
                    <li key={row.label} className="flex gap-2">
                      <span className={row.pass ? "text-emerald-300" : "text-amber-300"}>
                        {row.pass ? "✓" : "✗"}
                      </span>
                      {row.label}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <h2 className="text-sm font-semibold text-white">Business</h2>
                <ul className="mt-3 space-y-1.5 text-sm">
                  {Object.values(report.business || {}).map((row) => (
                    <li key={row.label} className="flex gap-2">
                      <span className={row.pass ? "text-emerald-300" : "text-amber-300"}>
                        {row.pass ? "✓" : "✗"}
                      </span>
                      {row.label}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <h2 className="text-sm font-semibold text-white">Was Sie korrigieren sollten</h2>
            <ul className="mt-3 space-y-2">
              {(report.findings || []).map((f) => (
                <li
                  key={f.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/5 bg-black/20 px-3 py-2.5 text-sm"
                >
                  <span>
                    <span className="mr-2 text-[10px] font-semibold uppercase text-zinc-500">
                      {f.severity}
                    </span>
                    {f.message}
                  </span>
                  {f.action?.kind === "coming" ? (
                    <span className="text-[10px] font-semibold uppercase text-zinc-500">
                      Coming {f.action.coming}
                    </span>
                  ) : f.action?.href ? (
                    <Link
                      href={f.action.href}
                      className="rounded-lg bg-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-100"
                    >
                      {f.action.label || "Open"}
                    </Link>
                  ) : null}
                </li>
              ))}
              {!report.findings?.length ? (
                <li className="text-sm text-zinc-500">Keine offenen Prioritäten.</li>
              ) : null}
            </ul>
          </section>

          {exportBase ? (
            <div className="flex flex-wrap gap-2">
              {(["pdf", "json", "csv", "markdown"] as const).map((fmt) => (
                <a
                  key={fmt}
                  href={`${exportBase}?format=${fmt}`}
                  className="rounded-xl border border-white/15 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-200 hover:bg-white/5"
                >
                  Export {fmt}
                </a>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
