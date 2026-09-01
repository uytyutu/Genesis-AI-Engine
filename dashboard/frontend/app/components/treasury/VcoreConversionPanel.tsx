"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_VCORE_IDENTITY,
  emptyPipeline,
  type ConversionPipelineState,
  type ConversionStage,
} from "../../lib/treasury/vcoreConversion";

const STAGE_ORDER: ConversionStage[] = [
  "IDENTITY",
  "WALLET",
  "DEX_DISCOVERY",
  "QUOTE",
  "SIMULATION",
  "SIGN",
  "BROADCAST",
  "CONFIRM",
  "REAL_SETTLEMENT",
];

function stageTone(s: "pending" | "pass" | "fail" | "skip") {
  switch (s) {
    case "pass":
      return "border-emerald-600 bg-emerald-950/50 text-emerald-300";
    case "fail":
      return "border-rose-700 bg-rose-950/40 text-rose-300";
    case "skip":
      return "border-zinc-700 bg-zinc-900 text-zinc-500";
    default:
      return "border-zinc-600 bg-zinc-900/80 text-zinc-400";
  }
}

export function VcoreConversionPanel() {
  const [amount, setAmount] = useState("1000");
  const [state, setState] = useState<ConversionPipelineState>(() => emptyPipeline());
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [walletHint, setWalletHint] = useState("не подключён");

  const push = (msg: string) => setLog((l) => [`${new Date().toLocaleTimeString("ru-RU")} · ${msg}`, ...l].slice(0, 30));

  const syncGenesisIdentity = useCallback(async () => {
    try {
      const res = await fetch("/api/treasury/vcore/genesis", { cache: "no-store" });
      const g = await res.json();
      if (!g.jettonMaster) return;
      setState((prev) => {
        const stages = { ...prev.stages };
        stages.IDENTITY = "pass";
        return {
          ...prev,
          stages,
          identity: {
            ...DEFAULT_VCORE_IDENTITY,
            jettonMaster: g.jettonMaster,
            status: "DEPLOYED_TESTNET",
            network: "ton-testnet",
            decimals: g.decimals || 9,
            note: `Testnet Genesis · supply ${g.totalSupplyOnChain ?? g.supplyHuman ?? "?"} · stage ${g.stage}. STON mainnet listing still separate.`,
          },
        };
      });
      push(`Genesis identity: ${g.jettonMaster} (${g.stage})`);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void syncGenesisIdentity();
  }, [syncGenesisIdentity]);

  const runDiscover = useCallback(async () => {
    setBusy(true);
    push("DEX discovery → STON.fi …");
    try {
      await syncGenesisIdentity();
      const res = await fetch("/api/treasury/vcore/discover", { cache: "no-store" });
      const data = await res.json();
      setState((prev) => {
        const stages = { ...prev.stages };
        stages.DEX_DISCOVERY = data.apiOk ? "pass" : "fail";
        // Prefer local Genesis identity over STON mainnet listing
        const genesisMaster = prev.identity.network === "ton-testnet" && prev.identity.jettonMaster;
        stages.IDENTITY = genesisMaster || data.vcoreFound ? "pass" : "fail";
        stages.QUOTE = "pending";
        stages.SIMULATION = "pending";
        stages.REAL_SETTLEMENT = "fail";
        return {
          ...prev,
          stages,
          identity: genesisMaster
            ? prev.identity
            : {
                ...DEFAULT_VCORE_IDENTITY,
                jettonMaster: data.vcoreAssetAddress,
                status: data.vcoreFound ? "UNKNOWN" : "GENESIS_DRAFT",
                network: data.vcoreFound ? "ton-mainnet" : "none",
                note: data.detail || DEFAULT_VCORE_IDENTITY.note,
              },
          discovery: {
            venue: data.venue || "STON.fi",
            apiOk: !!data.apiOk,
            routers: data.routers ?? 0,
            vcoreFound: !!data.vcoreFound,
            tonAssetAddress: data.tonAssetAddress,
            vcoreAssetAddress: data.vcoreAssetAddress,
            poolFound: !!data.poolFound,
            detail: data.detail || "",
          },
          quote: null,
          realSettlement: false,
        };
      });
      push(data.detail || "discovery done");
    } catch (e) {
      push(e instanceof Error ? e.message : "discovery error");
    } finally {
      setBusy(false);
    }
  }, [syncGenesisIdentity]);

  const runSimulate = useCallback(async () => {
    setBusy(true);
    push(`Simulate VCORE ${amount} → TON …`);
    try {
      const res = await fetch("/api/treasury/vcore/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount,
          vcoreAddress: state.identity.jettonMaster,
        }),
      });
      const data = await res.json();
      setState((prev) => {
        const stages = { ...prev.stages };
        const pass = data.simulation === "PASS";
        stages.QUOTE = pass ? "pass" : "fail";
        stages.SIMULATION = pass ? "pass" : "fail";
        stages.SIGN = pass && prev.walletConnected ? "pending" : "skip";
        stages.REAL_SETTLEMENT = "fail";
        return {
          ...prev,
          stages,
          quote: {
            from: data.from || "VCORE",
            to: data.to || "TON",
            amountIn: data.amountIn || amount,
            amountOut: data.amountOut,
            minReceive: data.minReceive,
            feeHint: data.feeHint,
            priceImpact: data.priceImpact,
            simulation: data.simulation || "FAIL",
            blocker: data.blocker || "SIMULATION_FAIL",
            message: data.message || "",
          },
        };
      });
      push(data.message || String(data.simulation));
    } catch (e) {
      push(e instanceof Error ? e.message : "simulate error");
    } finally {
      setBusy(false);
    }
  }, [amount, state.identity.jettonMaster]);

  const connectWallet = () => {
    // TON Connect wiring = next slice; honest stub that does not fake settlement
    setWalletHint("TON Connect: подготовлен UI — подпись только после Jetton+pool (см. docs.ton.org / TON Connect)");
    setState((prev) => ({
      ...prev,
      walletConnected: false,
      stages: { ...prev.stages, WALLET: "fail" },
    }));
    push(
      "CONNECT WALLET: без задеплоенного VCORE и пула подпись бесполезна. Интеграция TON Connect — следующий кирпич после Genesis Jetton.",
    );
  };

  const tryExchange = async () => {
    try {
      const killRes = await fetch("/api/treasury/vcore/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "prove",
        }),
      });
      const killJson = await killRes.json();
      const ks = killJson.killSwitch;
      if (!ks?.allowSend) {
        push(
          `KILL SWITCH ARMED — EXCHANGE blocked: ${(ks?.reasons || ["unknown"]).join(", ")}. Ничего не отправлено.`,
        );
        return;
      }
    } catch {
      push("KILL SWITCH: не удалось проверить — EXCHANGE отклонён по умолчанию.");
      return;
    }
    if (!state.quote || state.quote.simulation !== "PASS") {
      push("EXCHANGE отклонён: simulation ≠ PASS. Нет ликвидности / нет Jetton — TON из воздуха не создаётся.");
      return;
    }
    push("EXCHANGE: Kill Switch clear + sim PASS, но TON Connect ещё не подключён — REALIZED не нарисован.");
  };

  return (
    <section className="rounded-2xl border-2 border-violet-700/50 bg-gradient-to-b from-violet-950/40 to-zinc-950 p-5 space-y-4">
      <div>
        <p className="text-[10px] font-mono uppercase tracking-widest text-violet-400">Virtus Conversion Engine</p>
        <h2 className="mt-1 text-lg font-bold text-violet-200">VCORE → TON · закрыто до GENESIS PASS</h2>
        <p className="mt-2 max-w-3xl text-xs leading-relaxed text-zinc-400">
          Сейчас не этап conversion. После VERIFIED + EXTERNAL IDENTITY — только{" "}
          <strong className="text-zinc-200">DEX discovery</strong> (нашли ли VCORE / пул / quote). LP позже.
          Kill Switch блокирует EXCHANGE. REAL ledger не растёт от mint VCORE.
        </p>
      </div>

      {/* Pipeline strip */}
      <div className="flex flex-wrap gap-1.5">
        {STAGE_ORDER.map((st) => (
          <span key={st} className={`rounded border px-2 py-1 text-[9px] font-mono ${stageTone(state.stages[st])}`}>
            {st}
          </span>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Console card */}
        <div className="rounded-xl border border-zinc-700 bg-zinc-950/90 p-4 space-y-3 font-mono text-xs">
          <div className="grid grid-cols-[5rem_1fr] gap-2 items-center">
            <span className="text-zinc-500">FROM</span>
            <span className="text-violet-300">VCORE</span>
            <span className="text-zinc-500">AMOUNT</span>
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-emerald-300"
            />
            <span className="text-zinc-500">TO</span>
            <span className="text-cyan-300">TON</span>
            <span className="text-zinc-500">Route</span>
            <span className="text-zinc-300">VCORE → TON (STON.fi discovery)</span>
            <span className="text-zinc-500">Quote</span>
            <span className={state.quote?.amountOut ? "text-emerald-300" : "text-rose-300"}>
              {state.quote?.amountOut ?? "0.00… TON (нет маршрута / нет пула)"}
            </span>
            <span className="text-zinc-500">Min recv</span>
            <span className="text-zinc-400">{state.quote?.minReceive ?? "—"}</span>
            <span className="text-zinc-500">Sim</span>
            <span
              className={
                state.quote?.simulation === "PASS"
                  ? "text-emerald-400"
                  : state.quote
                    ? "text-rose-400"
                    : "text-zinc-500"
              }
            >
              {state.quote?.simulation ?? "—"} · {state.quote?.blocker ?? "pending"}
            </span>
            <span className="text-zinc-500">Wallet</span>
            <span className="text-zinc-400">{walletHint}</span>
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => void runDiscover()}
              className="rounded-lg bg-violet-700 px-3 py-2 text-[11px] font-bold text-zinc-50 disabled:opacity-50"
            >
              DEX DISCOVERY
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void runSimulate()}
              className="rounded-lg bg-cyan-700 px-3 py-2 text-[11px] font-bold text-zinc-950 disabled:opacity-50"
            >
              SIMULATE
            </button>
            <button
              type="button"
              onClick={connectWallet}
              className="rounded-lg border border-zinc-600 px-3 py-2 text-[11px] text-zinc-200"
            >
              CONNECT WALLET
            </button>
            <button
              type="button"
              onClick={tryExchange}
              className="rounded-lg bg-emerald-800/80 px-3 py-2 text-[11px] font-bold text-emerald-100"
            >
              EXCHANGE
            </button>
          </div>

          <div
            className={`rounded-lg border px-3 py-2 text-[11px] ${
              state.realSettlement
                ? "border-emerald-600 text-emerald-300"
                : "border-rose-900/80 text-rose-300/90"
            }`}
          >
            REAL SETTLEMENT: {state.realSettlement ? "YES" : "NO"} — только после on-chain confirm + рост TON
            balance.
          </div>
        </div>

        {/* Analysis */}
        <div className="space-y-3 text-xs">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 space-y-1">
            <h3 className="font-semibold text-zinc-200">Identity</h3>
            <p>Status: <span className="text-amber-300">{state.identity.status}</span></p>
            <p className="font-mono text-[10px] text-zinc-500">
              master: {state.identity.jettonMaster || "null"}
            </p>
            <p className="text-zinc-400">{state.identity.note}</p>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 space-y-1">
            <h3 className="font-semibold text-zinc-200">Discovery</h3>
            {state.discovery ? (
              <>
                <p>
                  {state.discovery.venue} · API {state.discovery.apiOk ? "OK" : "DOWN"} · routers{" "}
                  {state.discovery.routers}
                </p>
                <p>
                  VCORE listed: {String(state.discovery.vcoreFound)} · pool:{" "}
                  {String(state.discovery.poolFound)}
                </p>
                <p className="text-zinc-400">{state.discovery.detail}</p>
              </>
            ) : (
              <p className="text-zinc-500">Нажмите DEX DISCOVERY</p>
            )}
          </div>
          <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-3 text-amber-100/90">
            <h3 className="font-semibold">Что мы имеем сейчас (честно)</h3>
            <ul className="mt-1 list-disc pl-4 space-y-1 text-[11px]">
              <li>{state.farmNote}</li>
              <li>Вариант D (триллион VCORE → TON без пула) на честной DEX = невозможно.</li>
              <li>Вариант A/C: сначала Jetton + LP, потом STON simulate + TON Connect.</li>
              <li>Value Hunter / Compute — параллельные треки; не смешивать с «эмиссией денег».</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="max-h-36 overflow-y-auto rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-[10px] text-zinc-400 space-y-1">
        {log.length === 0 && <p>Журнал эксперимента пуст.</p>}
        {log.map((l) => (
          <div key={l}>{l}</div>
        ))}
      </div>
    </section>
  );
}
