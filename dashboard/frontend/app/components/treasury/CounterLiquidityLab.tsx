"use client";

import { useCallback, useState } from "react";

type Counts = {
  opportunities?: number;
  verified_sources?: number;
  zero_capital_filter_pass?: number;
  counter_liquidity_verified?: number;
  executable?: number;
  realized?: number;
  hypotheses?: number;
  rejected?: number;
  counter_invariant?: string;
};

type Report = {
  ok?: boolean;
  outcome?: string;
  message?: string;
  counts?: Counts;
  vcore?: { stage?: string; jettonMaster?: string | null; genesis_pass?: boolean };
  rejected?: { opportunityId?: string; status?: string; reject_reason?: string; protocol?: string; counterAsset?: string }[];
  hypotheses?: { opportunityId?: string; protocol?: string; evidence?: string; status?: string }[];
  counter_liquidity_verified?: unknown[];
  next_test?: string;
  law?: string[];
  error?: string;
};

export function CounterLiquidityLab() {
  const [data, setData] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<"discovery" | "hypotheses" | "rejected" | "reality">("discovery");

  const run = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/value-hunter/liquidity/discover", { cache: "no-store" });
      const json = (await res.json()) as Report;
      if (!res.ok || json.ok === false) setErr(json.error || `HTTP ${res.status}`);
      else setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, []);

  const c = data?.counts;

  return (
    <section className="rounded-2xl border-2 border-cyan-800/50 bg-gradient-to-b from-cyan-950/30 to-zinc-950 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-cyan-500">
            Counter-Liquidity Discovery Engine v1.0 · STRICT €0 · no account
          </p>
          <h2 className="mt-1 text-lg font-bold text-cyan-50">ЛАБОРАТОРИЯ ВСТРЕЧНОЙ ЛИКВИДНОСТИ</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            Гипотеза: может ли VCORE получить реальную встречную ликвидность при OWN_CAPITAL=€0 без заявки/KYC/депозита?
            NO — валидный научный результат. IMPLIED ≠ EXECUTABLE. Grants с proposal → REJECT.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void run()}
          className="rounded-lg bg-cyan-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
        >
          {busy ? "Поиск…" : "DISCOVER"}
        </button>
      </div>

      <div className="grid gap-2 sm:grid-cols-4 lg:grid-cols-7 text-[11px]">
        {[
          ["Возможности", c?.opportunities],
          ["Источники", c?.verified_sources],
          ["Strict €0", c?.zero_capital_filter_pass],
          ["Counter-liq", c?.counter_liquidity_verified],
          ["Executable", c?.executable ?? 0],
          ["Гипотезы", c?.hypotheses],
          ["Отклонено", c?.rejected],
        ].map(([l, v]) => (
          <div key={String(l)} className="rounded-lg border border-zinc-700 bg-zinc-950/70 p-3">
            <p className="font-mono text-zinc-500">{l}</p>
            <p className="mt-1 text-xl font-bold text-cyan-100">{v ?? "—"}</p>
          </div>
        ))}
      </div>

      {data?.message && (
        <p className="rounded-lg border border-cyan-900/40 bg-cyan-950/20 px-3 py-2 text-xs text-cyan-100">{data.message}</p>
      )}
      {data?.vcore && (
        <p className="font-mono text-[10px] text-zinc-500">
          Genesis stage={data.vcore.stage} · master={String(data.vcore.jettonMaster)} · PASS=
          {String(data.vcore.genesis_pass)} · outcome={data.outcome} · invariant={c?.counter_invariant}
        </p>
      )}
      {err && <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}

      <div className="flex flex-wrap gap-1">
        {(
          [
            ["discovery", "DISCOVERY"],
            ["hypotheses", "ГИПОТЕЗЫ"],
            ["rejected", "ОТКЛОНЕНО"],
            ["reality", "REALITY"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`rounded border px-2.5 py-1 text-[10px] font-mono ${
              tab === id ? "border-cyan-500 bg-cyan-950 text-cyan-100" : "border-zinc-700 text-zinc-400"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "discovery" && (
        <ul className="text-xs text-zinc-400 space-y-1">
          {(data?.law || []).map((l) => (
            <li key={l}>• {l}</li>
          ))}
          <li className="text-amber-200/90">Следующий тест: {data?.next_test || "—"}</li>
          <li>Кнопки: DISCOVER · VERIFY SOURCE · CHECK LIQUIDITY · SIMULATE — без AUTO EXECUTE</li>
        </ul>
      )}

      {tab === "hypotheses" && (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full text-left text-[11px]">
            <thead className="bg-zinc-900/80 font-mono text-zinc-500">
              <tr>
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Протокол</th>
                <th className="px-2 py-2">Evidence</th>
                <th className="px-2 py-2">Статус</th>
              </tr>
            </thead>
            <tbody>
              {(data?.hypotheses || []).map((h) => (
                <tr key={h.opportunityId} className="border-t border-zinc-800">
                  <td className="px-2 py-2 font-mono">{h.opportunityId}</td>
                  <td className="px-2 py-2">{h.protocol}</td>
                  <td className="px-2 py-2 text-zinc-500 max-w-md">{h.evidence}</td>
                  <td className="px-2 py-2 text-amber-200">{h.status}</td>
                </tr>
              ))}
              {!data?.hypotheses?.length && (
                <tr>
                  <td colSpan={4} className="px-3 py-3 text-zinc-500">
                    Нажмите DISCOVER
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "rejected" && (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full text-left text-[11px]">
            <thead className="bg-zinc-900/80 font-mono text-zinc-500">
              <tr>
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Протокол</th>
                <th className="px-2 py-2">Статус</th>
                <th className="px-2 py-2">Почему</th>
              </tr>
            </thead>
            <tbody>
              {(data?.rejected || []).map((r) => (
                <tr key={r.opportunityId} className="border-t border-zinc-800">
                  <td className="px-2 py-2 font-mono">{r.opportunityId}</td>
                  <td className="px-2 py-2">{r.protocol}</td>
                  <td className="px-2 py-2 text-amber-200">{r.status}</td>
                  <td className="px-2 py-2 text-zinc-500">{r.reject_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "reality" && (
        <p className="text-xs text-zinc-400">
          REAL_EXTERNAL_ASSETS = 0 · Reality Ledger только confirmed tx + causality (source→tx→recipient→delta). Testnet
          swap ≠ mainnet доход.
        </p>
      )}

      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run liquidity:discover</code>
      </p>
    </section>
  );
}
