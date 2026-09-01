"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  AssetScanRow,
  GenesisPassChecklist,
  HypothesisRecord,
  KillSwitchState,
  OpportunityRow,
  ProvenanceCertificate,
  RealityLedgerSnapshot,
  ValueProofReport,
} from "../../lib/treasury/vcoreResearch";
import type { ValueEngineSnapshot, ValueLayer } from "../../lib/treasury/vcoreValueEngine";
import { emptyValueEngine } from "../../lib/treasury/vcoreValueEngine";

type Tab = "hypothesis" | "prove" | "scanner" | "provenance" | "ledger" | "opportunities";

type ResearchSnap = {
  genesisPass?: GenesisPassChecklist;
  layers?: ValueEngineSnapshot;
  provenance?: ProvenanceCertificate;
  ledger?: RealityLedgerSnapshot;
  hypotheses?: HypothesisRecord[];
  opportunities?: OpportunityRow[];
  killSwitch?: KillSwitchState;
  genesis?: { stage?: string; jettonMaster?: string | null; blockers?: string[] };
  priority?: string[];
};

function layerList(layers?: ValueEngineSnapshot): ValueLayer[] {
  const L = layers || emptyValueEngine();
  return [L.declared, L.model, L.market, L.executable, L.realSettlement];
}

export function VcoreResearchLab() {
  const [tab, setTab] = useState<Tab>("hypothesis");
  const [snap, setSnap] = useState<ResearchSnap | null>(null);
  const [proof, setProof] = useState<ValueProofReport | null>(null);
  const [assets, setAssets] = useState<AssetScanRow[]>([]);
  const [provMsg, setProvMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [kill, setKill] = useState<KillSwitchState | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/treasury/vcore/research", { cache: "no-store" });
      const json = (await res.json()) as ResearchSnap;
      setSnap(json);
      setKill(json.killSwitch || null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "research load failed");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const post = async (action: string, extra?: Record<string, unknown>) => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/treasury/vcore/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...extra }),
      });
      const json = await res.json();
      if (action === "prove") {
        setProof(json.proof);
        setKill(json.killSwitch);
        if (json.hypotheses) setSnap((s) => (s ? { ...s, hypotheses: json.hypotheses } : s));
      }
      if (action === "scan") setAssets(json.assets || []);
      if (action === "verify" || action === "provenance") {
        setProvMsg(json.message);
        setSnap((s) => (s ? { ...s, provenance: json.certificate } : s));
      }
      if (action === "kill") setKill(json.killSwitch);
      if (action === "ledger" && json.ledger) setSnap((s) => (s ? { ...s, ledger: json.ledger } : s));
      if (action === "opportunities")
        setSnap((s) => (s ? { ...s, opportunities: json.opportunities } : s));
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "action failed");
    } finally {
      setBusy(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "hypothesis", label: "HYPOTHESIS" },
    { id: "prove", label: "VALUE PROOF" },
    { id: "scanner", label: "SCANNER" },
    { id: "provenance", label: "PROVENANCE" },
    { id: "ledger", label: "REALITY LEDGER" },
    { id: "opportunities", label: "OPPORTUNITY" },
  ];

  const gp = snap?.genesisPass;

  return (
    <section className="rounded-2xl border-2 border-fuchsia-800/50 bg-gradient-to-b from-fuchsia-950/25 to-zinc-950 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-fuchsia-400">
            Hypothesis Lab · Research Platform
          </p>
          <h2 className="mt-1 text-lg font-bold text-fuchsia-100">
            До LP: доказать происхождение стоимости, не нарисовать её
          </h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400">
            DECLARED / MODEL / MARKET / EXECUTABLE / REALIZED — пять отдельных строк. Kill Switch режет
            любую отправку при сомнении. Genesis PASS обязателен до testnet liquidity.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void post("kill", { emergency: true })}
            className="rounded-lg bg-rose-800 px-3 py-2 text-[11px] font-bold text-rose-50 disabled:opacity-50"
          >
            EMERGENCY STOP
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void load()}
            className="rounded-lg border border-fuchsia-700 px-3 py-2 text-[11px] text-fuchsia-100"
          >
            REFRESH
          </button>
        </div>
      </div>

      {/* Kill switch banner */}
      <div
        className={`rounded-lg border px-3 py-2 text-[11px] font-mono ${
          kill?.allowSend
            ? "border-emerald-700 text-emerald-300"
            : "border-rose-700 bg-rose-950/40 text-rose-200"
        }`}
      >
        KILL SWITCH: {kill?.allowSend ? "CLEAR (send still gated by Genesis+sim)" : "ARMED"} ·{" "}
        {(kill?.reasons || ["—"]).join(" · ")} · allowSend={String(kill?.allowSend ?? false)}
      </div>

      {/* Genesis PASS checklist */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-950/80 p-3">
        <h3 className="text-xs font-semibold text-zinc-200">GENESIS PASS checklist</h3>
        <div className="mt-2 grid gap-1 sm:grid-cols-2 text-[11px] font-mono">
          {(
            [
              ["Jetton master deployed", gp?.jettonMasterDeployed],
              ["Contract address verified", gp?.contractAddressVerified],
              ["Supply read from blockchain", gp?.supplyReadFromChain],
              ["Wallet owns VCORE", gp?.walletOwnsVcore],
              ["Transfer confirmed", gp?.transferConfirmed],
              ["Explorer confirms", gp?.explorerLinksPresent],
              ["Virtus reads independently", gp?.virtusReadsIndependently],
              ["EXTERNAL VERIFICATION", gp?.externalIdentityVerified],
              ["REAL SETTLEMENT = NO (frozen)", gp?.realSettlementIsNo],
            ] as const
          ).map(([label, ok]) => (
            <div key={label} className={ok ? "text-emerald-400" : "text-zinc-500"}>
              [{ok ? "x" : " "}] {label}
            </div>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-amber-200/90">
          allPass={String(gp?.allPass ?? false)} · stage={snap?.genesis?.stage || "?"} · До PASS: только
          Faucet→Deploy→Transfer→Verify. Research/Conversion/LP закрыты.
        </p>
      </div>

      {!gp?.allPass && (
        <div className="rounded-lg border border-zinc-600 bg-zinc-900/80 px-3 py-2 text-[11px] text-zinc-300">
          <strong className="text-zinc-100">GATE LOCK:</strong> Hypothesis / Value Proof / Scanner /
          Conversion — просмотр OK, исполнение закрыто до GENESIS PASS. Сейчас цель одна:{" "}
          <span className="font-mono text-cyan-300">WAITING_FAUCET → … → VERIFIED</span>
        </div>
      )}

      <div className="flex flex-wrap gap-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded border px-2.5 py-1.5 text-[10px] font-mono ${
              tab === t.id
                ? "border-fuchsia-500 bg-fuchsia-950 text-fuchsia-100"
                : "border-zinc-700 text-zinc-400"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {err && <p className="text-xs text-rose-400">{err}</p>}

      {/* Actions soft-locked until genesis pass — view still works */}
      {tab === "prove" && !gp?.allPass && (
        <p className="text-[11px] text-amber-200/80">
          PROVE VALUE доступен как read-only эксперимент, но маршрут до Jetton = FAIL. Не открывает LP.
        </p>
      )}

      {tab === "hypothesis" && (
        <div className="space-y-2">
          {(snap?.hypotheses || []).map((h) => (
            <div key={h.id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-mono font-bold text-fuchsia-200">
                  {h.id} · {h.title}
                </span>
                <span className="font-mono text-[10px] text-amber-300">{h.status}</span>
              </div>
              <p className="mt-1 text-zinc-400">METHOD: {h.method}</p>
              <p className="text-zinc-400">OBS: {h.observation}</p>
              <p className="text-zinc-500">
                EVIDENCE: {h.blockchainEvidence.length ? h.blockchainEvidence.join(" · ") : "—"}
              </p>
              <p className="text-zinc-300">RESULT: {h.result || "pending"}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "prove" && (
        <div className="space-y-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => void post("prove")}
            className="rounded-lg bg-fuchsia-700 px-4 py-2 text-xs font-bold text-zinc-50 disabled:opacity-50"
          >
            PROVE VALUE
          </button>
          <div className="grid gap-2 sm:grid-cols-2">
            {layerList(proof?.layers || snap?.layers).map((L) => (
              <div
                key={L.label}
                className="flex justify-between rounded border border-zinc-800 px-3 py-2 text-[11px] font-mono"
              >
                <span className="text-zinc-400">{L.label}</span>
                <span className={L.amount > 0 && L.label.includes("REAL") ? "text-emerald-300" : "text-amber-200"}>
                  {L.amount} {L.unit}
                </span>
              </div>
            ))}
          </div>
          {proof && (
            <div className="rounded-lg border border-zinc-700 bg-black/40 p-3 font-mono text-[11px] space-y-1 text-zinc-300">
              <div>Route: {proof.route || "—"}</div>
              <div>Quote: {proof.quote || "—"}</div>
              <div>Fees: {proof.fees || "—"}</div>
              <div>Slippage: {proof.slippage || "—"}</div>
              <div>Expected TON: {proof.expectedTon || "0"}</div>
              <div className={proof.simulation === "PASS" ? "text-emerald-400" : "text-rose-400"}>
                Simulation: {proof.simulation} · {proof.blocker}
              </div>
              <div className="text-zinc-500">{proof.message}</div>
            </div>
          )}
        </div>
      )}

      {tab === "scanner" && (
        <div className="space-y-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => void post("scan")}
            className="rounded-lg bg-cyan-800 px-4 py-2 text-xs font-bold text-cyan-50"
          >
            RUN UNIVERSAL ASSET SCAN
          </button>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-[11px]">
              <thead className="text-zinc-500 font-mono">
                <tr>
                  <th className="py-1 pr-2">Asset</th>
                  <th className="py-1 pr-2">Network</th>
                  <th className="py-1 pr-2">VCORE route</th>
                  <th className="py-1 pr-2">Liquidity</th>
                  <th className="py-1">Status</th>
                </tr>
              </thead>
              <tbody>
                {(assets.length ? assets : []).map((r) => (
                  <tr key={`${r.asset}-${r.network}`} className="border-t border-zinc-800 text-zinc-300">
                    <td className="py-1.5 pr-2 font-mono">{r.asset}</td>
                    <td className="py-1.5 pr-2">{r.network}</td>
                    <td className="py-1.5 pr-2">{r.vcoreRoute}</td>
                    <td className="py-1.5 pr-2">{r.liquidity}</td>
                    <td className="py-1.5 font-mono text-cyan-300">{r.status}</td>
                  </tr>
                ))}
                {!assets.length && (
                  <tr>
                    <td colSpan={5} className="py-3 text-zinc-500">
                      Нажмите SCAN — Virtus сам ищет маршруты, без заранее заданного пула.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "provenance" && (
        <div className="space-y-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => void post("verify")}
            className="rounded-lg bg-emerald-800 px-4 py-2 text-xs font-bold text-emerald-50"
          >
            VERIFY VCORE
          </button>
          {provMsg && (
            <p
              className={`font-mono text-sm ${
                snap?.provenance?.verified ? "text-emerald-300" : "text-rose-300"
              }`}
            >
              {provMsg}
            </p>
          )}
          <ol className="list-decimal space-y-1 pl-5 text-xs text-zinc-300">
            {(snap?.provenance?.chain || []).map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ol>
          <p className="text-[11px] text-zinc-500">
            Blockers: {(snap?.provenance?.blockers || []).join(", ") || "none"}
          </p>
        </div>
      )}

      {tab === "ledger" && (
        <div className="grid gap-3 md:grid-cols-3 text-xs">
          <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3">
            <p className="font-mono text-amber-300">MODEL</p>
            <p className="mt-2 text-2xl font-bold text-amber-100">
              ${snap?.ledger?.model.usd?.toLocaleString() ?? "1,000,000"}
            </p>
            <p className="mt-1 text-[10px] text-zinc-500">{snap?.ledger?.model.note}</p>
          </div>
          <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-3">
            <p className="font-mono text-emerald-300">REAL (FROZEN)</p>
            <p className="mt-2 text-lg font-bold text-emerald-100">
              {snap?.ledger?.real.ton ?? 0} TON
            </p>
            <p className="text-lg font-bold text-emerald-100">{snap?.ledger?.real.btc ?? 0} BTC</p>
            <p className="mt-1 text-[10px] text-zinc-500">
              Заморожено на 0. Mint VCORE не меняет REAL. Только confirmed external receipt.
            </p>
          </div>
          <div className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
            <p className="font-mono text-zinc-300">TRANSACTIONS</p>
            <ul className="mt-2 space-y-1 text-[11px] text-zinc-400">
              {(snap?.ledger?.transactions || []).length === 0 && <li>Пусто — нет confirmed REAL tx</li>}
              {(snap?.ledger?.transactions || []).map((tx) => (
                <li key={tx.id}>
                  {tx.id} · {tx.kind} · {tx.hash || "no hash"} · confirmed={String(tx.confirmed)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {tab === "opportunities" && (
        <div className="space-y-2">
          <div className="rounded-lg border border-zinc-700 bg-zinc-950/60 p-3 text-[11px] text-zinc-400 space-y-1">
            <p className="font-semibold text-zinc-200">Target Settlement · 300 BTC</p>
            <p>
              TARGET ASSET: BTC · TARGET AMOUNT: <strong className="text-amber-200">300</strong> · MAX
              CAPITAL: €0. Mint VCORE ≠ право на 300 BTC. Если ликвидность 0.0001 — показываем 0.0001.
              Mainnet execution закрыт. Доказательство = Bitcoin UTXO / txid.
            </p>
            <p className="text-zinc-500">
              CLI: <code className="text-cyan-300">npm run vcore:pipeline</code> → шаг T (settlementStatus).
            </p>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void post("opportunities")}
            className="rounded-lg border border-zinc-600 px-3 py-1.5 text-[11px] text-zinc-200"
          >
            Refresh opportunities
          </button>
          {(snap?.opportunities || []).map((o) => (
            <div key={o.id} className="rounded-lg border border-zinc-800 p-3 text-[11px] space-y-1">
              <div className="flex justify-between gap-2">
                <span className="font-semibold text-zinc-200">{o.channel}</span>
                <span className="font-mono text-cyan-400">{o.status}</span>
              </div>
              <p>Capital: €{o.capitalRequiredEur} · Gas: €{o.gasRequiredEur}</p>
              <p>Reward: {o.rewardHint}</p>
              <p>Expected net: {o.expectedNet}</p>
              <p className="text-zinc-500">Risk: {o.risk}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
