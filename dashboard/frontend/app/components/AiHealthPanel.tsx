"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Module = {
  id: string;
  label: string;
  status: string;
  coming?: string;
  detail?: string;
};

type AiHealthPayload = {
  ok: boolean;
  title: string;
  modules: Module[];
  live_count: number;
  total: number;
  note?: string;
};

type Props = { dark?: boolean };

function moduleStatusLabel(m: Module): string {
  if (m.status === "live") return "Verfügbar";
  if (m.status === "waiting") return "Nicht aktiviert";
  if (m.status === "coming") return "Coming Soon";
  return "Status nicht verfügbar";
}

function moduleStatusTone(m: Module, dark: boolean): string {
  if (m.status === "live") return dark ? "text-emerald-300" : "text-emerald-700";
  if (m.status === "waiting") return dark ? "text-zinc-500" : "text-slate-400";
  if (m.status === "coming") return dark ? "text-violet-300/80" : "text-violet-700";
  return dark ? "text-zinc-600" : "text-slate-400";
}

export function AiHealthPanel({ dark = true }: Props) {
  const [data, setData] = useState<AiHealthPayload | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "unavailable">("loading");

  const load = useCallback(async () => {
    if (!getClientToken()) {
      setState("unavailable");
      return;
    }
    setState("loading");
    try {
      const res = await fetch(`${API}/api/client/vector/ai-health`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (res.ok) {
        setData((await res.json()) as AiHealthPayload);
        setState("ready");
        return;
      }
      setData(null);
      setState("unavailable");
    } catch {
      setData(null);
      setState("unavailable");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (state === "loading") {
    return (
      <section
        className={`rounded-3xl border p-5 ${
          dark
            ? "border-white/10 bg-white/[0.03]"
            : "border-slate-200 bg-white/80 shadow-sm"
        }`}
        aria-label="AI Health"
        data-vector-ai-health
      >
        <p className={`text-sm ${dark ? "text-zinc-500" : "text-slate-500"}`}>
          Modulstatus wird geladen…
        </p>
      </section>
    );
  }

  if (state === "unavailable" || !data) {
    return (
      <section
        className={`rounded-3xl border p-5 ${
          dark
            ? "border-white/10 bg-white/[0.03]"
            : "border-slate-200 bg-white/80 shadow-sm"
        }`}
        aria-label="AI Health"
        data-vector-ai-health
      >
        <p
          className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${
            dark ? "text-sky-300/80" : "text-sky-800"
          }`}
        >
          AI Health
        </p>
        <p className={`mt-2 text-sm ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          Status nicht verfügbar — Verbindung zum Workspace konnte den Modulstatus
          nicht laden.
        </p>
      </section>
    );
  }

  const availableCount = data.modules.filter((m) => m.status === "live").length;

  return (
    <section
      className={`rounded-3xl border p-5 ${
        dark
          ? "border-white/10 bg-white/[0.03]"
          : "border-slate-200 bg-white/80 shadow-sm"
      }`}
      aria-label="AI Health"
      data-vector-ai-health
    >
      <div className="flex items-end justify-between gap-3">
        <div>
          <p
            className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${
              dark ? "text-sky-300/80" : "text-sky-800"
            }`}
          >
            {data.title}
          </p>
          <p className={`mt-1 text-sm ${dark ? "text-zinc-400" : "text-slate-600"}`}>
            Welche Module wirklich verfügbar sind — ohne dekorative Live-Badges
          </p>
        </div>
        <p className={`text-sm tabular-nums ${dark ? "text-zinc-400" : "text-slate-500"}`}>
          {availableCount}/{data.total} verfügbar
        </p>
      </div>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.modules.map((m) => {
          const label = moduleStatusLabel(m);
          return (
            <li
              key={m.id}
              className={`flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm ${
                dark ? "bg-black/20" : "bg-slate-50"
              }`}
            >
              <span className={moduleStatusTone(m, dark)} aria-hidden>
                {m.status === "live" ? "✓" : m.status === "coming" ? "◷" : "○"}
              </span>
              <span className="min-w-0 flex-1">
                <span className="font-medium">{m.label}</span>
                <span
                  className={`ml-2 text-[10px] font-semibold uppercase ${moduleStatusTone(m, dark)}`}
                >
                  {label}
                </span>
                {m.detail ? (
                  <span
                    className={`mt-0.5 block text-[11px] ${
                      dark ? "text-zinc-500" : "text-slate-500"
                    }`}
                  >
                    {m.detail}
                  </span>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
      {data.note ? (
        <p className={`mt-3 text-[11px] ${dark ? "text-zinc-600" : "text-slate-400"}`}>
          {data.note}
        </p>
      ) : null}
    </section>
  );
}
