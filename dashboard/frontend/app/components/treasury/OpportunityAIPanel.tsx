"use client";

import { useCallback, useState } from "react";

type TopRow = {
  id?: string;
  priority?: string;
  verdict?: string;
  action?: string;
  failed_gates?: string[];
  failed_economic?: string[];
  origin?: string;
};

type SystematicReport = {
  ok?: boolean;
  epoch_status?: string;
  scientific_result?: string;
  message?: string;
  thesis?: string;
  priority_order?: string[];
  counts?: {
    mechanisms_scanned?: number;
    working_brick_candidates?: number;
    frictionless_incomplete?: number;
    filtered_out?: number;
    real_external_assets?: number;
  };
  compute_capability?: { vectors_per_sec?: number | null; income_claimed?: boolean };
  top_compute_first?: TopRow[];
  agent_policy?: { may_end_epoch_with?: string; must_not?: string };
  error?: string;
};

export function OpportunityAIPanel() {
  const [data, setData] = useState<SystematicReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(async (offline: boolean) => {
    setBusy(true);
    setErr(null);
    try {
      const q = offline ? "?offline=1" : "";
      const res = await fetch(`/api/opportunity/systematic${q}`, { cache: "no-store" });
      const json = (await res.json()) as SystematicReport;
      if (!res.ok || json.ok === false) setErr(json.error || `HTTP ${res.status}`);
      else setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, []);

  const epoch = data?.epoch_status;
  const honest = epoch === "NO_VALID_OPPORTUNITY";
  const candidate = epoch === "CANDIDATE_FOUND";

  return (
    <section className="rounded-2xl border-2 border-cyan-800/40 bg-gradient-to-b from-cyan-950/30 to-zinc-950 p-5 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-cyan-400">
            Opportunity AI · Systematic Economic Discovery
          </p>
          <h2 className="mt-1 text-lg font-bold text-cyan-50">ВНЕШНЯЯ СТОИМОСТЬ → КОШЕЛЁК (не BALANCE=$1M)</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            Воронка: публичные механизмы → €0 / без account·KYC·application·deposit·purchase·stake →
            полный brick (ACTION…TRANSFERABILITY). Статусы: INCOMPLETE → CANDIDATE_REAL → REAL (только после TX).
            Честный конец: <span className="font-mono text-amber-200">NO_VALID_OPPORTUNITY</span>.
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
            className="rounded-lg bg-cyan-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Discovery…" : "SYSTEMATIC DISCOVER"}
          </button>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-4 text-[11px]">
        <div
          className={`rounded-lg border p-3 ${
            honest
              ? "border-amber-700/50 bg-amber-950/20"
              : candidate
                ? "border-emerald-700/50 bg-emerald-950/20"
                : "border-zinc-700"
          }`}
        >
          <p className="font-mono text-zinc-500">epoch_status</p>
          <p className="text-sm font-bold text-cyan-50 break-all">{epoch ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">working_bricks</p>
          <p className="text-xl font-bold text-cyan-100">{data?.counts?.working_brick_candidates ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">REAL_EXTERNAL</p>
          <p className="text-xl font-bold text-rose-200">{data?.counts?.real_external_assets ?? 0}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">vectors/s ≠ income</p>
          <p className="text-xl font-bold text-zinc-300">{data?.compute_capability?.vectors_per_sec ?? "—"}</p>
        </div>
      </div>

      {data?.message && (
        <p className={`text-xs leading-relaxed ${honest ? "text-amber-100/90" : "text-zinc-300"}`}>{data.message}</p>
      )}

      {data?.priority_order && (
        <p className="font-mono text-[10px] text-zinc-500">priority: {data.priority_order.join(" → ")}</p>
      )}

      {(data?.top_compute_first || []).length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full text-left text-[10px] text-zinc-300">
            <thead className="bg-zinc-900 text-zinc-500">
              <tr>
                <th className="px-2 py-2">id</th>
                <th className="px-2 py-2">priority</th>
                <th className="px-2 py-2">verdict</th>
                <th className="px-2 py-2">failed</th>
              </tr>
            </thead>
            <tbody>
              {(data?.top_compute_first || []).slice(0, 10).map((r) => (
                <tr key={r.id || `${r.priority}-${r.verdict}`} className="border-t border-zinc-800">
                  <td className="px-2 py-1.5 font-mono">{r.id || "—"}</td>
                  <td className="px-2 py-1.5">{r.priority}</td>
                  <td className="px-2 py-1.5">{r.verdict}</td>
                  <td className="px-2 py-1.5 text-zinc-500">
                    {[...(r.failed_gates || []), ...(r.failed_economic || [])].join(", ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {err && <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}
      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run opportunity:systematic</code> · политика:{" "}
        {data?.agent_policy?.may_end_epoch_with || "NO_VALID_OPPORTUNITY"} · не{" "}
        {data?.agent_policy?.must_not || "force-confirm hypothesis"}
      </p>
    </section>
  );
}
