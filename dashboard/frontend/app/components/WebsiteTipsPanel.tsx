"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import type { VectorAction } from "../lib/vectorSurfaceContext";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

export type WebsiteTip = {
  id: string;
  category: string;
  severity: string;
  message: string;
  done?: boolean;
  action?: VectorAction;
};

export type WebsiteTipsPayload = {
  ok: boolean;
  score?: number;
  niche?: string;
  tips?: WebsiteTip[];
  open_tips?: WebsiteTip[];
  summary?: { total: number; open: number; done: number };
  honesty?: string;
  error?: string;
};

type AuditorReport = {
  ok: boolean;
  report_id?: string;
  overall_business_score?: number;
  website?: Record<string, number>;
  findings?: {
    id: string;
    message: string;
    severity: string;
    action?: VectorAction;
  }[];
  ai_summary?: string;
};

type Props = {
  orderId: string;
  dark?: boolean;
};

const CAT_LABEL: Record<string, string> = {
  legal: "Legal",
  seo: "SEO",
  performance: "Performance",
  content: "Content",
};

async function downloadExport(orderId: string, format: string): Promise<void> {
  const res = await fetch(
    `${API}/api/client/orders/${orderId}/vc-auditor/export?format=${format}`,
    { headers: { ...clientAuthHeaders() } },
  );
  if (!res.ok) throw new Error("export_failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `virtus-core-website-auditor_${orderId}.${format === "markdown" ? "md" : format}`;
  a.click();
  URL.revokeObjectURL(url);
}

export function WebsiteTipsPanel({ orderId, dark = true }: Props) {
  const [data, setData] = useState<WebsiteTipsPayload | null>(null);
  const [audit, setAudit] = useState<AuditorReport | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!getClientToken() || !orderId) return;
    setLoading(true);
    try {
      const [tipsRes, auditRes] = await Promise.all([
        fetch(`${API}/api/client/orders/${orderId}/website-tips`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        }),
        fetch(`${API}/api/client/orders/${orderId}/vc-auditor?locale=de`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        }),
      ]);
      if (tipsRes.ok) setData((await tipsRes.json()) as WebsiteTipsPayload);
      if (auditRes.ok) setAudit((await auditRes.json()) as AuditorReport);
    } catch {
      setData({ ok: false, error: "load_failed", tips: [] });
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !data && !audit) {
    return (
      <p className={`text-sm ${dark ? "text-zinc-500" : "text-slate-500"}`}>
        Virtus Core Website Auditor prüft Ihre Website…
      </p>
    );
  }

  if (!data?.ok && !audit?.ok) {
    return (
      <div
        className={`rounded-2xl border p-5 text-sm ${
          dark ? "border-white/10 text-zinc-400" : "border-slate-200 text-slate-600"
        }`}
      >
        <p>Noch kein Website-Paket zum Prüfen gefunden.</p>
        <Link href="/client/products" className="mt-2 inline-block text-emerald-400 hover:underline">
          Meine Produkte →
        </Link>
      </div>
    );
  }

  const tips = data?.tips || [];
  const findings = audit?.findings || [];

  return (
    <div className="space-y-5">
      {audit?.ok ? (
        <section
          className={`rounded-3xl border p-5 sm:p-6 ${
            dark
              ? "border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-transparent"
              : "border-emerald-200 bg-emerald-50/50"
          }`}
        >
          <p
            className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${
              dark ? "text-emerald-300/80" : "text-emerald-800"
            }`}
          >
            Virtus Core Website Auditor
          </p>
          <p className="mt-1 text-sm opacity-70">Overall Business Score</p>
          <p className="text-4xl font-semibold tabular-nums">
            {audit.overall_business_score}
            <span className="text-lg opacity-50"> / 100</span>
          </p>
          <p className={`mt-3 text-sm leading-relaxed ${dark ? "text-zinc-300" : "text-slate-700"}`}>
            {audit.ai_summary}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(audit.website || {}).map(([k, v]) => (
              <div key={k}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="font-medium">{k.toUpperCase()}</span>
                  <span className="tabular-nums opacity-60">{v}</span>
                </div>
                <div className={`h-1.5 rounded-full ${dark ? "bg-white/10" : "bg-slate-200"}`}>
                  <div
                    className="h-full rounded-full bg-emerald-400"
                    style={{ width: `${v}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {(["pdf", "markdown", "json", "csv"] as const).map((fmt) => (
              <button
                key={fmt}
                type="button"
                className={`rounded-xl border px-3 py-1.5 text-xs font-semibold uppercase ${
                  dark
                    ? "border-white/15 text-zinc-200 hover:bg-white/5"
                    : "border-slate-200 text-slate-700"
                }`}
                onClick={() => void downloadExport(orderId, fmt)}
              >
                Export {fmt}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {findings.length ? (
        <section
          className={`rounded-3xl border p-5 ${
            dark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white"
          }`}
        >
          <h2 className="text-sm font-semibold">Findings · Fix with Vector</h2>
          <ul className="mt-3 space-y-2">
            {findings.map((f) => (
              <li
                key={f.id}
                className={`flex flex-wrap items-center justify-between gap-2 rounded-xl px-3 py-2.5 text-sm ${
                  dark ? "bg-black/20" : "bg-slate-50"
                }`}
              >
                <span>{f.message}</span>
                {f.action?.kind === "coming" ? (
                  <span className="text-[10px] font-semibold uppercase opacity-50">
                    Coming {f.action.coming || "R3.2"}
                  </span>
                ) : (
                  <span
                    className={`rounded-lg px-2 py-1 text-xs font-semibold ${
                      dark ? "bg-emerald-500/20 text-emerald-100" : "bg-emerald-100 text-emerald-900"
                    }`}
                  >
                    {f.action?.label || "Исправить"}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section
        className={`rounded-3xl border p-5 sm:p-6 ${
          dark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white shadow-sm"
        }`}
        data-vector-website-tips
      >
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p
              className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${
                dark ? "text-emerald-300/80" : "text-emerald-800"
              }`}
            >
              Website Admin · Tips
            </p>
            <p className="mt-1 text-lg font-semibold">{data?.niche || "Your website"}</p>
          </div>
          <p className="text-3xl font-semibold tabular-nums">
            {data?.score ?? 0}
            <span className="text-lg opacity-60">/100</span>
          </p>
        </div>

        <ul className="mt-5 space-y-2">
          {tips.map((tip) => (
            <li
              key={tip.id}
              className={`flex flex-wrap items-start gap-3 rounded-2xl border px-3 py-3 ${
                dark ? "border-white/5 bg-black/20" : "border-slate-100 bg-slate-50"
              }`}
            >
              <span
                className={
                  tip.done
                    ? dark
                      ? "text-emerald-300"
                      : "text-emerald-700"
                    : dark
                      ? "text-amber-300"
                      : "text-amber-700"
                }
              >
                {tip.done ? "✓" : "·"}
              </span>
              <div className="min-w-0 flex-1">
                <p
                  className={`text-[10px] font-semibold uppercase tracking-wide ${
                    dark ? "text-zinc-500" : "text-slate-500"
                  }`}
                >
                  {CAT_LABEL[tip.category] || tip.category}
                </p>
                <p className="text-sm">{tip.message}</p>
              </div>
              {tip.action && !tip.done ? (
                <button
                  type="button"
                  disabled={tip.action.kind === "coming"}
                  className={`shrink-0 rounded-xl px-3 py-1.5 text-xs font-semibold ${
                    tip.action.kind === "coming"
                      ? dark
                        ? "bg-white/5 text-zinc-500"
                        : "bg-slate-100 text-slate-500"
                      : dark
                        ? "bg-emerald-500/25 text-emerald-100"
                        : "bg-emerald-700 text-white"
                  }`}
                >
                  {tip.action.kind === "coming"
                    ? `Coming ${tip.action.coming || "R3.2"}`
                    : tip.action.label}
                </button>
              ) : null}
            </li>
          ))}
        </ul>

        {data?.honesty ? (
          <p className={`mt-4 text-[11px] ${dark ? "text-zinc-600" : "text-slate-400"}`}>
            {data.honesty}
          </p>
        ) : null}
      </section>
    </div>
  );
}
