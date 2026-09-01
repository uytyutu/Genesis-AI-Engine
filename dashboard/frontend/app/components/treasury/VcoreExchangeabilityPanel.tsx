"use client";

import { useCallback, useState } from "react";

type StepRow = { status?: string; [key: string]: unknown };

type Report = {
  ok?: boolean;
  goal?: string;
  axiom?: string;
  cex_disclaimer?: string;
  chain_model?: string[];
  summary?: {
    REAL_EXTERNAL_ASSET?: string;
    readiness?: string;
    experiment_outcome?: string;
    pass_count?: number;
    not_yet_count?: number;
  };
  stages?: Record<string, StepRow>;
  lab_status?: Record<string, string>;
  next?: string;
  error?: string;
};

export function VcoreExchangeabilityPanel() {
  const [data, setData] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(async (offline: boolean) => {
    setBusy(true);
    setErr(null);
    try {
      const q = offline ? "?offline=1" : "";
      const res = await fetch(`/api/treasury/vcore/exchangeability${q}`, { cache: "no-store" });
      const json = (await res.json()) as Report;
      if (!res.ok || json.ok === false) setErr(json.error || `HTTP ${res.status}`);
      else setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, []);

  const steps = data?.stages ? Object.entries(data.stages) : [];

  return (
    <section className="rounded-2xl border-2 border-amber-800/50 bg-gradient-to-b from-amber-950/30 to-zinc-950 p-5 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-amber-400">
            VCORE-X01 · External Exchangeability · primary track
          </p>
          <h2 className="mt-1 text-lg font-bold text-amber-50">CONTRACT → DEX → LIQUIDITY → SWAP → TXID</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            Доказываем: identity → compatibility → market → liquidity → swap → external asset → TXID.
            REAL_EXTERNAL_ASSET=PASS только после X01.10. Не VCORE=€1, не painted liquidity, не Virtus-only swap.
            P-03 Golem frozen.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(true)}
            className="rounded-lg border border-zinc-600 bg-zinc-900 px-3 py-2 text-xs font-bold text-zinc-200 disabled:opacity-50"
          >
            Offline
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(false)}
            className="rounded-lg bg-amber-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Assess…" : "EXCHANGEABILITY"}
          </button>
        </div>
      </div>

      {data?.goal && (
        <p className="rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-100/90">
          {data.goal}
        </p>
      )}

      <div className="grid gap-2 sm:grid-cols-3 text-[11px]">
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">REAL_EXTERNAL</p>
          <p className="font-bold text-amber-100">{data?.summary?.REAL_EXTERNAL_ASSET ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">readiness</p>
          <p className="text-zinc-200 break-all text-[10px]">{data?.summary?.readiness ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">outcome</p>
          <p className="text-zinc-200 break-all text-[10px]">{data?.summary?.experiment_outcome ?? "—"}</p>
        </div>
      </div>

      {steps.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-zinc-800 max-h-72 overflow-y-auto">
          <table className="w-full text-left text-[10px] text-zinc-300">
            <thead className="sticky top-0 bg-zinc-900 text-zinc-500">
              <tr>
                <th className="px-2 py-2">step</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">detail</th>
              </tr>
            </thead>
            <tbody>
              {steps.map(([name, row]) => (
                <tr key={name} className="border-t border-zinc-800">
                  <td className="px-2 py-1.5 font-mono">{row.code ? `${row.code}` : name}</td>
                  <td
                    className={`px-2 py-1.5 font-bold ${
                      row.status === "PASS"
                        ? "text-emerald-300"
                        : row.status === "NOT_YET"
                          ? "text-amber-200"
                          : "text-rose-300"
                    }`}
                  >
                    {String(row.status)}
                  </td>
                  <td className="px-2 py-1.5 text-zinc-500">
                    {String(row.name || "")}
                    {name.includes("LIQUIDITY") ? " · no paint" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.cex_disclaimer && <p className="text-[10px] text-zinc-500">{data.cex_disclaimer}</p>}
      {data?.next && <p className="text-[10px] text-zinc-500">{data.next}</p>}
      {data?.lab_status && (
        <p className="font-mono text-[10px] text-zinc-600">
          lab: {Object.entries(data.lab_status).map(([k, v]) => `${k}=${v}`).join(" · ")}
        </p>
      )}
      {err && <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}
      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run vcore:x01</code>
      </p>
    </section>
  );
}
