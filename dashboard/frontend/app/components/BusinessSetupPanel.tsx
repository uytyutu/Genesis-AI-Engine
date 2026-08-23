"use client";

import { useCallback, useEffect, useState } from "react";
import type { StoreAdminSectionId } from "./StoreAdminShell";
import type { BusinessSetupPayload, VectorAction } from "../lib/vectorSurfaceContext";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Props = {
  dark?: boolean;
  /** When embedded in Store Admin, section navigation stays in-page */
  onNavigateSection?: (section: StoreAdminSectionId) => void;
  compact?: boolean;
};

function runAction(
  action: VectorAction | undefined,
  onNavigateSection?: (section: StoreAdminSectionId) => void,
) {
  if (!action) return;
  if (action.kind === "navigate_section" && action.section && onNavigateSection) {
    onNavigateSection(action.section as StoreAdminSectionId);
    return;
  }
  if (action.kind === "navigate_href" && action.href) {
    window.location.href = action.href;
  }
}

export function BusinessSetupPanel({
  dark = true,
  onNavigateSection,
  compact = false,
}: Props) {
  const [data, setData] = useState<BusinessSetupPayload | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) return;
    try {
      const res = await fetch(`${API}/api/client/vector/business-setup`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (res.ok) setData((await res.json()) as BusinessSetupPayload);
    } catch {
      /* optional */
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (!data) return null;

  return (
    <section
      className={`rounded-3xl border ${
        dark
          ? "border-white/10 bg-white/[0.03]"
          : "border-slate-200 bg-white/80 shadow-sm"
      } ${compact ? "p-4" : "p-5 sm:p-6"}`}
      aria-label="Business Setup"
      data-vector-business-setup
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p
            className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${
              dark ? "text-emerald-300/80" : "text-emerald-800"
            }`}
          >
            {data.launch?.title || data.title}
          </p>
          <p className={`mt-1 text-sm ${dark ? "text-zinc-400" : "text-slate-600"}`}>
            {data.launch?.stage === "growth"
              ? "Сайт запущен — следующий уровень развития"
              : "Пошаговый запуск цифрового бизнеса"}
          </p>
        </div>
        <p className="text-3xl font-semibold tabular-nums tracking-tight">
          {data.pct}
          <span className="text-lg opacity-60">%</span>
        </p>
      </div>

      <div
        className={`mt-4 h-2 overflow-hidden rounded-full ${
          dark ? "bg-white/10" : "bg-slate-200"
        }`}
        role="progressbar"
        aria-valuenow={data.pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`h-full rounded-full ${
            dark
              ? "bg-gradient-to-r from-sky-400 to-emerald-400"
              : "bg-gradient-to-r from-sky-600 to-emerald-600"
          }`}
          style={{ width: `${Math.min(100, Math.max(0, data.pct))}%` }}
        />
      </div>

      {data.launch?.items?.length ? (
        <ul className="mt-5 space-y-2">
          {data.launch.items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => {
                  if (item.href) window.location.href = item.href;
                }}
                className={`flex w-full flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left transition ${
                  dark ? "hover:bg-white/[0.04]" : "hover:bg-slate-50"
                }`}
              >
                <span className="flex items-center gap-2 text-sm font-medium">
                  <span
                    className={
                      item.done
                        ? dark
                          ? "text-emerald-300"
                          : "text-emerald-700"
                        : dark
                          ? "text-zinc-500"
                          : "text-slate-400"
                    }
                  >
                    {item.done ? "✅" : item.upsell ? "⚪" : "🟡"}
                  </span>
                  {item.label}
                  {item.upsell ? (
                    <span className="text-[10px] uppercase text-amber-400/90">модуль</span>
                  ) : null}
                </span>
                {item.why ? (
                  <span className={`pl-6 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
                    {item.why}
                  </span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {data.launch?.next ? (
        <a
          href={data.launch.next.href || "/client"}
          className={`mt-4 inline-flex rounded-xl px-4 py-2.5 text-sm font-semibold ${
            dark
              ? "bg-emerald-500/90 text-black hover:bg-emerald-400"
              : "bg-emerald-700 text-white"
          }`}
        >
          Начать: {data.launch.next.label}
        </a>
      ) : null}

      {data.launch?.note ? (
        <p className={`mt-3 text-[11px] ${dark ? "text-zinc-600" : "text-slate-400"}`}>
          {data.launch.note}
        </p>
      ) : null}

      {!compact && data.bars?.length ? (
        <details className="mt-4">
          <summary
            className={`cursor-pointer text-xs font-semibold uppercase tracking-wide ${
              dark ? "text-zinc-500" : "text-slate-500"
            }`}
          >
            Техническая готовность ({data.pct}%)
          </summary>
          <ul className="mt-3 space-y-2.5">
            {data.bars.map((bar) => (
              <li key={bar.id}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="font-medium">{bar.label}</span>
                  <span className={`tabular-nums ${dark ? "text-zinc-500" : "text-slate-500"}`}>
                    {bar.pct}%
                  </span>
                </div>
                <div
                  className={`h-1.5 overflow-hidden rounded-full ${
                    dark ? "bg-white/10" : "bg-slate-200"
                  }`}
                >
                  <div
                    className={`h-full rounded-full ${
                      bar.done
                        ? dark
                          ? "bg-emerald-400"
                          : "bg-emerald-600"
                        : dark
                          ? "bg-sky-400/80"
                          : "bg-sky-600"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, bar.pct))}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      {data.note && !data.launch?.note ? (
        <p className={`mt-3 text-[11px] ${dark ? "text-zinc-600" : "text-slate-400"}`}>
          {data.note}
        </p>
      ) : null}
    </section>
  );
}
