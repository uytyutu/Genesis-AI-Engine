"use client";

import type { StoreAdminSectionId } from "./StoreAdminShell";
import type { StoreSetupStatus, VectorSetupStep, VectorTip } from "../lib/vectorSurfaceContext";

type Props = {
  status: StoreSetupStatus | null;
  loading?: boolean;
  dark?: boolean;
  compact?: boolean;
  onNavigate: (section: StoreAdminSectionId) => void;
};

function asSection(id: string | undefined): StoreAdminSectionId | null {
  const allowed: StoreAdminSectionId[] = [
    "dashboard",
    "products",
    "orders",
    "customers",
    "commerce",
    "payments",
    "shipping",
    "integrations",
    "marketing",
    "analytics",
    "design",
    "settings",
  ];
  if (id && (allowed as string[]).includes(id)) return id as StoreAdminSectionId;
  return null;
}

export function StoreAdminVectorGuidance({
  status,
  loading,
  dark = true,
  compact = false,
  onNavigate,
}: Props) {
  if (loading && !status) {
    return (
      <div
        className={`rounded-3xl border px-4 py-3 text-sm ${
          dark
            ? "border-white/10 bg-white/[0.03] text-zinc-500"
            : "border-slate-200 bg-white/80 text-slate-500"
        }`}
      >
        Vector is checking your store setup…
      </div>
    );
  }

  if (!status) return null;

  const pct = status.readiness_pct;
  const next = status.next_step;
  const tip = status.tips[0] as VectorTip | undefined;

  if (compact) {
    return (
      <div
        className={`flex flex-wrap items-center gap-3 rounded-2xl border px-3 py-2.5 text-xs ${
          dark
            ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-100"
            : "border-emerald-200 bg-emerald-50 text-emerald-950"
        }`}
      >
        <span className="font-semibold tracking-wide">Vector</span>
        <span
          className={`tabular-nums font-semibold ${
            dark ? "text-emerald-200" : "text-emerald-800"
          }`}
        >
          {pct}%
        </span>
        <span className={`min-w-0 flex-1 truncate ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          {tip?.message || status.vector.greeting}
        </span>
        {tip ? (
          <button
            type="button"
            className={`shrink-0 rounded-lg px-2.5 py-1 font-semibold transition ${
              dark
                ? "bg-emerald-500/25 hover:bg-emerald-500/35"
                : "bg-emerald-600/15 hover:bg-emerald-600/25"
            }`}
            onClick={() => {
              const sec = asSection(tip.section);
              if (sec) onNavigate(sec);
            }}
          >
            {tip.cta_label || "Open"}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <section
      className={`overflow-hidden rounded-3xl border ${
        dark
          ? "border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-sky-500/5"
          : "border-emerald-200/80 bg-gradient-to-br from-emerald-50 via-white to-sky-50/40 shadow-sm"
      }`}
      aria-label="Vector store setup"
      data-vector-surface="store_admin"
    >
      <div className="p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p
              className={`text-[11px] font-semibold uppercase tracking-[0.22em] ${
                dark ? "text-emerald-300/80" : "text-emerald-800"
              }`}
            >
              Vector · Store setup
            </p>
            <p className="mt-2 max-w-xl text-sm leading-relaxed sm:text-base">
              {status.vector.greeting}
            </p>
          </div>
          <div className="text-right">
            <p
              className={`text-[10px] font-semibold uppercase tracking-wider ${
                dark ? "text-zinc-500" : "text-slate-500"
              }`}
            >
              Store readiness
            </p>
            <p className="mt-1 text-3xl font-semibold tabular-nums tracking-tight">
              {pct}
              <span className="text-lg opacity-60">%</span>
            </p>
            <p className={`text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
              Setup focus {status.setup_pct}%
            </p>
          </div>
        </div>

        <div
          className={`mt-4 h-2 overflow-hidden rounded-full ${
            dark ? "bg-white/10" : "bg-slate-200/80"
          }`}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Store readiness"
        >
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              dark
                ? "bg-gradient-to-r from-sky-400 to-emerald-400"
                : "bg-gradient-to-r from-sky-600 to-emerald-600"
            }`}
            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          />
        </div>

        <ol className="mt-5 grid gap-2 sm:grid-cols-2">
          {status.steps.map((step: VectorSetupStep) => (
            <li
              key={step.id}
              className={`flex items-center gap-2.5 rounded-2xl border px-3 py-2.5 text-sm ${
                dark
                  ? "border-white/5 bg-black/20"
                  : "border-slate-100 bg-white/70"
              }`}
            >
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  step.done
                    ? dark
                      ? "bg-emerald-500/25 text-emerald-200"
                      : "bg-emerald-100 text-emerald-800"
                    : dark
                      ? "bg-white/5 text-zinc-500"
                      : "bg-slate-100 text-slate-500"
                }`}
                aria-hidden
              >
                {step.done ? "✓" : "○"}
              </span>
              <span className="min-w-0 flex-1 truncate font-medium">{step.label}</span>
              {step.coming && !step.done ? (
                <span
                  className={`shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${
                    dark ? "bg-white/5 text-zinc-500" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {step.coming}
                </span>
              ) : null}
              {!step.done && step.actionable ? (
                <button
                  type="button"
                  className={`shrink-0 text-[11px] font-semibold ${
                    dark ? "text-emerald-300 hover:text-emerald-200" : "text-emerald-800"
                  }`}
                  onClick={() => {
                    const sec = asSection(step.section);
                    if (sec) onNavigate(sec);
                  }}
                >
                  {step.cta_label || "Open"}
                </button>
              ) : null}
            </li>
          ))}
        </ol>

        {tip ? (
          <div
            className={`mt-5 rounded-2xl border px-4 py-3 ${
              dark
                ? "border-white/10 bg-white/[0.04]"
                : "border-emerald-100 bg-emerald-50/60"
            }`}
          >
            <p className={`text-xs font-semibold ${dark ? "text-emerald-200" : "text-emerald-900"}`}>
              Vector tip
            </p>
            <p className={`mt-1 text-sm ${dark ? "text-zinc-300" : "text-slate-700"}`}>
              {tip.message}
            </p>
            <button
              type="button"
              className={`mt-3 rounded-xl px-3 py-2 text-xs font-semibold transition ${
                dark
                  ? "bg-emerald-500/25 text-emerald-100 hover:bg-emerald-500/35"
                  : "bg-emerald-700 text-white hover:bg-emerald-800"
              }`}
              onClick={() => {
                const sec = asSection(tip.section);
                if (sec) onNavigate(sec);
              }}
            >
              {tip.cta_label || "Continue"}
            </button>
          </div>
        ) : null}

        {next && !next.done ? (
          <p className={`mt-3 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            Next: {next.label}
            {status.note ? ` · ${status.note}` : ""}
          </p>
        ) : status.note ? (
          <p className={`mt-3 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            {status.note}
          </p>
        ) : null}
      </div>
    </section>
  );
}
