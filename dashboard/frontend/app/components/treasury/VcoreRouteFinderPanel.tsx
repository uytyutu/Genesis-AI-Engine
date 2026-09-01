"use client";

import { useCallback, useEffect, useState } from "react";

type RouteRow = {
  id: string;
  path: string[];
  version?: string;
  venue?: string;
  classification: string;
  expectedTon: number;
  expectedBtc: number;
  capitalRequiredEur: number;
  liquidityRequired: boolean;
  zeroCapital?: boolean;
  detail: string;
  quote?: string | null;
};

type Report = {
  analysisNote?: string;
  architecture?: Record<string, string>;
  routes?: RouteRow[];
  thor?: {
    ok?: boolean;
    btcSupported?: boolean;
    tonSupported?: boolean;
    vcoreOnThor?: boolean;
    availableCount?: number;
    note?: string;
  };
  ston?: { discovery?: { listed?: boolean; detail?: string }; simulation?: { simulation?: string; expectedTon?: string | null } };
  bestZeroCapital?: RouteRow | null;
  towardTarget300Btc?: { status?: string; expectedBtc?: number; gap?: number; message?: string };
  input?: { vcore?: string | null; stage?: string; amountHuman?: string };
};

const CLASS_TONE: Record<string, string> = {
  ZERO_CAPITAL_EXECUTABLE: "text-emerald-300 border-emerald-700",
  CAPITAL_REQUIRED: "text-amber-300 border-amber-700",
  LIQUIDITY_REQUIRED: "text-amber-200 border-amber-800",
  UNSUPPORTED: "text-zinc-400 border-zinc-600",
  NO_ROUTE: "text-rose-300 border-rose-900",
  SIMULATION_FAILED: "text-rose-300 border-rose-800",
  PROFITABLE: "text-cyan-300 border-cyan-700",
  UNPROFITABLE: "text-zinc-500 border-zinc-700",
};

export function VcoreRouteFinderPanel() {
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [metaHint, setMetaHint] = useState("проверяю MetaMask…");

  useEffect(() => {
    const eth = typeof window !== "undefined" ? (window as unknown as { ethereum?: { isMetaMask?: boolean } }).ethereum : undefined;
    if (eth?.isMetaMask) setMetaHint("MetaMask обнаружен (EVM). TON Jetton — отдельно через TON Connect / CLI.");
    else if (eth) setMetaHint("EVM-кошелёк есть. MetaMask флаг не виден.");
    else setMetaHint("MetaMask не найден в этом окне браузера.");
  }, []);

  const loadCached = useCallback(async () => {
    try {
      const res = await fetch("/api/treasury/vcore/routes", { cache: "no-store" });
      const json = await res.json();
      if (json.last) setReport(json.last);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void loadCached();
  }, [loadCached]);

  const runFind = async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/treasury/vcore/routes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: "1000000" }),
      });
      const json = await res.json();
      if (json.report) setReport(json.report);
      else setErr("Нет отчёта — проверьте CLI npm run vcore:routes");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "route find failed");
    } finally {
      setBusy(false);
    }
  };

  const t = report?.towardTarget300Btc;

  return (
    <section className="rounded-2xl border-2 border-sky-700/50 bg-gradient-to-b from-sky-950/40 to-zinc-950 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-sky-400">VCORE Route Finder v1</p>
          <h2 className="mt-1 text-lg font-bold text-sky-100">Граф маршрутов · Zero-Capital Mode</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            A: VCORE→TON · B: multi-hop · C: supported→THOR→BTC. Не рисуем 300 BTC. Без пула нет свопа. MetaMask ≠
            подпись TON Jetton.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void runFind()}
          className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
        >
          {busy ? "Ищем…" : "FIND ROUTES"}
        </button>
      </div>

      <div className="grid gap-2 md:grid-cols-3 text-[11px]">
        <div className="rounded-lg border border-zinc-700 bg-zinc-950/80 p-3">
          <p className="font-mono text-zinc-500">INPUT</p>
          <p className="mt-1 text-zinc-200">1 000 000 VCORE</p>
          <p className="text-zinc-500">stage: {report?.input?.stage || "—"}</p>
          <p className="break-all text-[10px] text-zinc-500">master: {report?.input?.vcore || "null"}</p>
        </div>
        <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3">
          <p className="font-mono text-amber-300">TARGET 300 BTC</p>
          <p className="mt-1 text-amber-100">{t?.status || "—"}</p>
          <p>expected: {t?.expectedBtc ?? 0} BTC · gap: {t?.gap ?? 300}</p>
          <p className="mt-1 text-[10px] text-zinc-500">{t?.message}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 bg-zinc-950/80 p-3">
          <p className="font-mono text-zinc-500">WALLETS</p>
          <p className="mt-1 text-emerald-300">{metaHint}</p>
          <p className="mt-1 text-[10px] text-zinc-500">
            ETH/BTC vault → MetaMask ниже. VCORE/TON → Genesis CLI + TON wallet после PASS.
          </p>
        </div>
      </div>

      {report?.architecture && (
        <div className="rounded-lg border border-zinc-800 bg-black/30 p-3 text-[11px] text-zinc-400 space-y-1 font-mono">
          <p>A · {report.architecture.A}</p>
          <p>B · {report.architecture.B}</p>
          <p>C · {report.architecture.C}</p>
        </div>
      )}

      {report?.thor && (
        <p className="text-[11px] text-zinc-400">
          THORChain: API {report.thor.ok ? "OK" : "DOWN"} · BTC pool {String(report.thor.btcSupported)} · TON{" "}
          {String(report.thor.tonSupported)} · VCORE on THOR: {String(report.thor.vcoreOnThor)} ·{" "}
          {report.thor.note}
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] text-left text-[11px]">
          <thead className="font-mono text-zinc-500">
            <tr>
              <th className="py-1 pr-2">Route</th>
              <th className="py-1 pr-2">Class</th>
              <th className="py-1 pr-2">Out</th>
              <th className="py-1 pr-2">Cap € / LP?</th>
              <th className="py-1">Detail</th>
            </tr>
          </thead>
          <tbody>
            {(report?.routes || []).map((r) => (
              <tr key={r.id} className="border-t border-zinc-800 align-top">
                <td className="py-2 pr-2 font-mono text-sky-200">{r.path.join(" → ")}</td>
                <td className="py-2 pr-2">
                  <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${CLASS_TONE[r.classification] || "text-zinc-400 border-zinc-700"}`}>
                    {r.classification}
                  </span>
                </td>
                <td className="py-2 pr-2 font-mono text-zinc-300">
                  {r.expectedTon || 0} TON
                  <br />
                  {r.expectedBtc || 0} BTC
                </td>
                <td className="py-2 pr-2 font-mono text-zinc-400">
                  {r.capitalRequiredEur} / {r.liquidityRequired ? "YES" : "no"}
                </td>
                <td className="py-2 text-zinc-500 max-w-md">{r.detail}</td>
              </tr>
            ))}
            {!report?.routes?.length && (
              <tr>
                <td colSpan={5} className="py-4 text-zinc-500">
                  Нажмите FIND ROUTES — движок опросит STON + THORNode без подделки котировок.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {err && <p className="text-xs text-rose-400">{err}</p>}
      <p className="text-[10px] text-zinc-600">
        Broadcast: never auto. REAL only after tx hash + confirm + balance increase.{" "}
        {report?.analysisNote}
      </p>
    </section>
  );
}
