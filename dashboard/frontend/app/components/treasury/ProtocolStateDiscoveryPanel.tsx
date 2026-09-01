"use client";

import { useCallback, useState } from "react";

type Autopsy = {
  id?: string;
  brick_status?: string;
  insight_fit?: boolean;
  missing?: string[];
  why_not_real_yet?: string[];
  state_machine?: { template?: string; experiment_ready?: boolean };
  kind?: string;
};

type PsdReport = {
  ok?: boolean;
  epoch_status?: string;
  scientific_result?: string;
  message?: string;
  research_question?: string;
  axiom?: string;
  insight_class?: string;
  counts?: {
    frictionless_autopsied?: number;
    incomplete_economic_brick?: number;
    candidate_real_brick?: number;
    real_external_asset?: number;
    insight_fit_compute_path?: number;
  };
  missing_field_frequency?: Record<string, number>;
  autopsy?: Autopsy[];
  insight_fit_ids?: string[];
  next?: string;
  error?: string;
};

export function ProtocolStateDiscoveryPanel() {
  const [data, setData] = useState<PsdReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(async (offline: boolean) => {
    setBusy(true);
    setErr(null);
    try {
      const q = offline ? "?offline=1" : "";
      const res = await fetch(`/api/protocol/discover${q}`, { cache: "no-store" });
      const json = (await res.json()) as PsdReport;
      if (!res.ok || json.ok === false) setErr(json.error || `HTTP ${res.status}`);
      else setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, []);

  const freq = Object.entries(data?.missing_field_frequency || {}).sort((a, b) => b[1] - a[1]);

  return (
    <section className="rounded-2xl border-2 border-indigo-800/40 bg-gradient-to-b from-indigo-950/30 to-zinc-950 p-5 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-indigo-400">
            Protocol State Discovery · insight-class
          </p>
          <h2 className="mt-1 text-lg font-bold text-indigo-50">COMPUTE → PROOF → STATE → REWARD</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            Не VCORE→обменник. Три ядра: Contract · State Transition · Reward Flow. Не взлом — публичные состояния
            и законная выплата. Аксиома: ликвидность не появляется из VCORE.
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
            className="rounded-lg bg-indigo-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Autopsy…" : "DEEP AUTOPSY"}
          </button>
        </div>
      </div>

      {data?.research_question && (
        <p className="rounded-lg border border-indigo-900/40 bg-indigo-950/20 px-3 py-2 text-[11px] text-indigo-100/90 leading-relaxed">
          Q: {data.research_question}
        </p>
      )}

      <div className="grid gap-2 sm:grid-cols-4 text-[11px]">
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">autopsied</p>
          <p className="text-xl font-bold text-indigo-100">{data?.counts?.frictionless_autopsied ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-3">
          <p className="font-mono text-zinc-500">INCOMPLETE</p>
          <p className="text-xl font-bold text-amber-100">{data?.counts?.incomplete_economic_brick ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">CANDIDATE_REAL</p>
          <p className="text-xl font-bold text-emerald-200">{data?.counts?.candidate_real_brick ?? 0}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">insight_fit (compute)</p>
          <p className="text-xl font-bold text-indigo-100">{data?.counts?.insight_fit_compute_path ?? "—"}</p>
        </div>
      </div>

      {data?.message && <p className="text-xs text-zinc-300 leading-relaxed">{data.message}</p>}

      {freq.length > 0 && (
        <p className="font-mono text-[10px] text-zinc-500">
          missing fields: {freq.map(([k, v]) => `${k}×${v}`).join(" · ")}
        </p>
      )}

      {(data?.autopsy || []).length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-zinc-800 max-h-80 overflow-y-auto">
          <table className="w-full text-left text-[10px] text-zinc-300">
            <thead className="sticky top-0 bg-zinc-900 text-zinc-500">
              <tr>
                <th className="px-2 py-2">id</th>
                <th className="px-2 py-2">brick</th>
                <th className="px-2 py-2">machine</th>
                <th className="px-2 py-2">why not REAL</th>
              </tr>
            </thead>
            <tbody>
              {(data?.autopsy || []).map((a) => (
                <tr
                  key={a.id}
                  className={`border-t border-zinc-800 ${a.insight_fit ? "bg-indigo-950/30" : ""}`}
                >
                  <td className="px-2 py-1.5 font-mono">
                    {a.id}
                    {a.insight_fit ? " ★" : ""}
                  </td>
                  <td className="px-2 py-1.5">{a.brick_status}</td>
                  <td className="px-2 py-1.5">{a.state_machine?.template}</td>
                  <td className="px-2 py-1.5 text-zinc-500">{(a.why_not_real_yet || []).slice(0, 2).join("; ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.insight_fit_ids && data.insight_fit_ids.length > 0 && (
        <p className="text-[10px] text-indigo-200/80">
          Compute-path leads: {data.insight_fit_ids.join(", ")} — нужны конкретные контракты, не классы.
        </p>
      )}

      {data?.next && <p className="text-[10px] text-zinc-500">{data.next}</p>}
      {err && <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}
      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run protocol:discover</code> · REAL_EXTERNAL только после TXID
      </p>
    </section>
  );
}
