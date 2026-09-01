"use client";

import { useCallback, useEffect, useState } from "react";
import {
  emptyValueEngine,
  type ValueEngineSnapshot,
  type ValueLayer,
} from "../../lib/treasury/vcoreValueEngine";

type GenesisPayload = {
  stage?: string;
  status?: string;
  network?: string;
  adminAddress?: string | null;
  probeAddress?: string | null;
  jettonMaster?: string | null;
  totalSupplyOnChain?: string | null;
  adminBalanceOnChain?: string | null;
  probeBalanceOnChain?: string | null;
  tonBalance?: number | null;
  blockers?: string[];
  explorer?: Record<string, string>;
  faucetHint?: string;
  gates?: { lpAllowed?: boolean; mainnetAllowed?: boolean };
  valueLayers?: ValueEngineSnapshot | Record<string, ValueLayer>;
  cli?: Record<string, string>;
  detail?: string;
  verified?: boolean;
  identityPass?: boolean;
  log?: string[];
  externalVerification?: {
    status?: string;
    identity?: string | null;
    mismatches?: string[];
    comparedAt?: string | null;
    remote?: { contractDeployed?: boolean; totalSupplyOnChain?: string | null } | null;
  };
};

const GENESIS_STAGES = [
  "NOT_STARTED",
  "WAITING_FAUCET",
  "FUNDED",
  "DEPLOYED",
  "MINTED",
  "TRANSFERRED",
  "VERIFIED",
] as const;

function layerRows(layers: GenesisPayload["valueLayers"]): ValueLayer[] {
  if (!layers) return Object.values(emptyValueEngine());
  const order = ["declared", "model", "market", "executable", "realSettlement"] as const;
  return order.map((k) => {
    const raw = (layers as Record<string, ValueLayer>)[k];
    if (raw && typeof raw === "object" && "label" in raw) return raw;
    return emptyValueEngine()[k === "realSettlement" ? "realSettlement" : k];
  });
}

export function VcoreGenesisPanel() {
  const [data, setData] = useState<GenesisPayload | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/treasury/vcore/genesis", { cache: "no-store" });
      const json = (await res.json()) as GenesisPayload;
      setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "genesis fetch failed");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const stage = data?.stage || "NOT_STARTED";
  const layers = layerRows(data?.valueLayers);

  return (
    <section className="rounded-2xl border-2 border-cyan-800/60 bg-gradient-to-b from-cyan-950/30 to-zinc-950 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-cyan-500">
            VCORE Genesis · TON testnet
          </p>
          <h2 className="mt-1 text-lg font-bold text-cyan-200">
            Identity gate — Wallet → Mint → Transfer → Verify
          </h2>
          <p className="mt-2 max-w-3xl text-xs leading-relaxed text-zinc-400">
            Один кирпич: доказать Jetton on-chain. LP и mainnet закрыты. Value Engine считает слои{" "}
            <strong className="text-zinc-200">отдельно</strong> — модельный миллион ≠ executable TON.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void refresh()}
          className="rounded-lg border border-cyan-700 px-3 py-2 text-[11px] font-semibold text-cyan-200 disabled:opacity-50"
        >
          REFRESH STATE
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {GENESIS_STAGES.map((s) => {
          const idx = GENESIS_STAGES.indexOf(s);
          const cur = GENESIS_STAGES.indexOf(stage as (typeof GENESIS_STAGES)[number]);
          const pass = cur >= idx && stage !== "NOT_STARTED";
          const active = s === stage;
          return (
            <span
              key={s}
              className={`rounded border px-2 py-1 text-[9px] font-mono ${
                active
                  ? "border-cyan-500 bg-cyan-950 text-cyan-200"
                  : pass
                    ? "border-emerald-700 bg-emerald-950/40 text-emerald-300"
                    : "border-zinc-700 text-zinc-500"
              }`}
            >
              {s}
            </span>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-700 bg-zinc-950/90 p-4 font-mono text-[11px] space-y-2">
          <div className="grid grid-cols-[7rem_1fr] gap-2">
            <span className="text-zinc-500">Status</span>
            <span className="text-cyan-300">{data?.status || "—"}</span>
            <span className="text-zinc-500">Network</span>
            <span className="text-zinc-300">{data?.network || "ton-testnet"}</span>
            <span className="text-zinc-500">Admin</span>
            <span className="break-all text-zinc-300">{data?.adminAddress || "null"}</span>
            <span className="text-zinc-500">Master</span>
            <span className="break-all text-emerald-300">{data?.jettonMaster || "null"}</span>
            <span className="text-zinc-500">Supply</span>
            <span className="text-emerald-300">{data?.totalSupplyOnChain ?? "—"} VCORE</span>
            <span className="text-zinc-500">Admin bal</span>
            <span className="text-zinc-300">{data?.adminBalanceOnChain ?? "—"}</span>
            <span className="text-zinc-500">Probe bal</span>
            <span className="text-zinc-300">{data?.probeBalanceOnChain ?? "—"}</span>
            <span className="text-zinc-500">Blockers</span>
            <span className="text-rose-300">{(data?.blockers || []).join(", ") || "none"}</span>
            <span className="text-zinc-500">External</span>
            <span
              className={
                data?.externalVerification?.identity === "IDENTITY_VERIFIED"
                  ? "text-emerald-300"
                  : data?.externalVerification?.identity === "IDENTITY_MISMATCH"
                    ? "text-rose-300"
                    : "text-zinc-400"
              }
            >
              {data?.externalVerification?.identity ||
                data?.externalVerification?.status ||
                "PENDING (после verify)"}
            </span>
          </div>
          {data?.explorer?.master && (
            <a
              href={data.explorer.master}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-cyan-400 underline"
            >
              Open master on tonviewer (testnet)
            </a>
          )}
          {err && <p className="text-rose-400">{err}</p>}
        </div>

        <div className="space-y-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 space-y-2">
            <h3 className="text-xs font-semibold text-zinc-200">Value Engine (слои не смешивать)</h3>
            {layers.map((L) => (
              <div
                key={L.label}
                className="flex items-baseline justify-between gap-2 border-b border-zinc-800/80 py-1 text-[11px]"
              >
                <span className="font-mono text-zinc-400">{L.label}</span>
                <span
                  className={
                    L.amount > 0 && L.label !== "REAL SETTLEMENT" && L.label.includes("DECLARED")
                      ? "text-amber-300"
                      : L.amount > 0 && L.label === "MODEL VALUE"
                        ? "text-amber-300"
                        : L.amount > 0
                          ? "text-emerald-300"
                          : "text-zinc-500"
                  }
                >
                  {L.amount} {L.unit}
                </span>
              </div>
            ))}
            <p className="text-[10px] text-zinc-500">
              Цель эксперимента позже: MODEL &gt; 0 и REAL SETTLEMENT &gt; 0 одновременно. Сейчас REAL = 0
              (нет swap). LP gate: {String(data?.gates?.lpAllowed ?? false)}.
            </p>
          </div>

          <div className="rounded-xl border border-amber-900/50 bg-amber-950/20 p-3 text-[11px] text-amber-100/90 space-y-1">
            <p className="font-semibold">Owner path (локально, ключи не в UI)</p>
            <ol className="list-decimal pl-4 space-y-1 text-amber-100/80">
              <li>
                <code className="text-amber-200">npm run vcore:genesis:init</code> → адрес +{" "}
                <code>.env.ton</code>
              </li>
              <li>
                Faucet testnet TON → {data?.faucetHint || "https://t.me/testgiver_ton_bot"}
              </li>
              <li>
                <code className="text-amber-200">npm run vcore:genesis:deploy</code>
              </li>
              <li>
                <code className="text-amber-200">npm run vcore:genesis:transfer</code>
              </li>
              <li>
                <code className="text-amber-200">npm run vcore:genesis:verify</code> → REFRESH STATE
              </li>
            </ol>
            {data?.detail && <p className="pt-1 text-zinc-400">{data.detail}</p>}
          </div>
        </div>
      </div>

      {!!data?.log?.length && (
        <div className="max-h-28 overflow-y-auto rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-[10px] text-zinc-500 space-y-1">
          {data.log.slice(0, 8).map((l) => (
            <div key={l}>{l}</div>
          ))}
        </div>
      )}
    </section>
  );
}
