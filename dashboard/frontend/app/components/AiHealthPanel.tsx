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

export function AiHealthPanel({ dark = true }: Props) {
  const [data, setData] = useState<AiHealthPayload | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) return;
    try {
      const res = await fetch(`${API}/api/client/vector/ai-health`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (res.ok) setData((await res.json()) as AiHealthPayload);
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
            Which modules are live vs waiting
          </p>
        </div>
        <p className={`text-sm tabular-nums ${dark ? "text-zinc-400" : "text-slate-500"}`}>
          {data.live_count}/{data.total} live
        </p>
      </div>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.modules.map((m) => (
          <li
            key={m.id}
            className={`flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm ${
              dark ? "bg-black/20" : "bg-slate-50"
            }`}
          >
            <span
              className={
                m.status === "live"
                  ? dark
                    ? "text-emerald-300"
                    : "text-emerald-700"
                  : dark
                    ? "text-zinc-500"
                    : "text-slate-400"
              }
            >
              {m.status === "live" ? "✓" : "⏳"}
            </span>
            <span className="min-w-0 flex-1">
              <span className="font-medium">{m.label}</span>
              {m.coming ? (
                <span
                  className={`ml-2 text-[10px] font-semibold uppercase ${
                    dark ? "text-zinc-500" : "text-slate-400"
                  }`}
                >
                  {m.coming}
                </span>
              ) : null}
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
        ))}
      </ul>
      {data.note ? (
        <p className={`mt-3 text-[11px] ${dark ? "text-zinc-600" : "text-slate-400"}`}>
          {data.note}
        </p>
      ) : null}
    </section>
  );
}
