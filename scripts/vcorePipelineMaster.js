#!/usr/bin/env node
/**
 * Virtus VCORE Pipeline Master (honest) + Target Settlement Engine
 *
 * TARGET: 300 BTC · MAX CAPITAL: €0
 * A) Genesis / VCORE identity
 * B) DEX discover + simulate VCORE→TON
 * C) TON→BTC bridge adapter (blocked until REAL TON)
 * T) Target Settlement Engine — capacity vs 300 BTC (never paint)
 *
 *   npm run vcore:pipeline
 *   npm run vcore:pipeline -- --amount 1000 --btc bc1q...
 *
 * Mainnet execution: CLOSED. REAL_SETTLEMENT_CONFIRMED only after BTC UTXO proof.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { loadState } = require("./lib/vcoreGenesisCore");
const { executeVcoreToTonSwap } = require("./lib/vcoreDexSwap");
const { bridgeTonToBtc, readLedger } = require("./lib/vcoreBtcBridge");
const { evaluateTargetSettlement, DEFAULT_TARGET } = require("./lib/vcoreTargetSettlement");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, ".runtime", "vcore_pipeline_last.json");

function argValue(name, fallback = null) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return fallback;
}

function genesisGate(state) {
  const checks = {
    hasMaster: !!state.jettonMaster,
    stage: state.stage,
    external:
      state.externalVerification && state.externalVerification.identity === "IDENTITY_VERIFIED",
    supply: !!state.totalSupplyOnChain,
    adminBal: state.adminBalanceOnChain != null && Number(state.adminBalanceOnChain) > 0,
    verified: state.stage === "VERIFIED",
  };
  checks.pass =
    checks.hasMaster &&
    checks.external &&
    checks.supply &&
    checks.adminBal &&
    checks.verified;
  return checks;
}

async function run() {
  const amount = argValue("--amount", "1000000"); // full supply probe by default for target hunt
  const btc = argValue("--btc", process.env.VAULT_BTC_ADDRESS || "");
  const broadcast = process.argv.includes("--broadcast");
  const targetBtc = Number(argValue("--target-btc", String(DEFAULT_TARGET.amount)));

  const state = loadState();
  const ledger = readLedger();
  const gate = genesisGate(state);

  /** A — VCORE balance / identity */
  const stepA = {
    name: "A_CHECK_VCORE",
    jettonMaster: state.jettonMaster,
    adminAddress: state.adminAddress,
    adminBalanceOnChain: state.adminBalanceOnChain,
    totalSupplyOnChain: state.totalSupplyOnChain,
    stage: state.stage,
    externalVerification: state.externalVerification?.identity || "PENDING",
    genesisPass: gate.pass,
    realLedger: { ton: ledger.real?.ton ?? 0, btc: ledger.real?.btc ?? 0, frozen: !!ledger.frozen },
  };

  /** B — DEX (honest) */
  let stepB;
  if (!state.jettonMaster) {
    stepB = {
      name: "B_DEX_VCORE_TO_TON",
      status: "STOPPED",
      blocker: "WAITING_GENESIS",
      message: "No Jetton — faucet → deploy → transfer → verify first.",
      realSettlement: false,
    };
  } else {
    stepB = {
      name: "B_DEX_VCORE_TO_TON",
      ...(await executeVcoreToTonSwap({ amountHuman: amount, broadcast })),
    };
  }

  /** C — BTC bridge */
  const stepC = {
    name: "C_BRIDGE_TON_TO_BTC",
    ...(await bridgeTonToBtc({
      tonAmount: stepB.simulation?.expectedTon || "0",
      destinationBtcAddress: btc || "bc1q_OWNER_SET_LATER",
    })),
  };

  /** T — Target Settlement Engine (300 BTC / capital 0) */
  const stepT = evaluateTargetSettlement({
    genesisGate: gate,
    dexResult: stepB,
    bridgeResult: stepC,
    ledger,
    vcoreAvailable: state.adminBalanceOnChain || state.supplyHuman || "0",
    target: { asset: "BTC", amount: targetBtc, maxCapitalEur: 0 },
  });

  const report = {
    at: new Date().toISOString(),
    pipeline: "VCORE → route hunt → BTC target",
    target: { asset: "BTC", amount: targetBtc, maxCapitalEur: 0 },
    law: "PERMISSIONLESS_SETTLEMENT_LAW — never paint 300 BTC; UTXO proof only",
    mainnetExecution: false,
    broadcastRequested: broadcast,
    steps: { A: stepA, B: stepB, C: stepC, T: stepT },
    settlementStatus: stepT.status,
    discoverySummary: stepT.discovery,
    next: !gate.pass
      ? "Close Genesis Gate first (faucet → deploy → transfer → verify + EXTERNAL)"
      : stepT.status === "READY_FOR_OWNER"
        ? "OWNER APPROVAL only — still no auto broadcast / no mainnet"
        : stepT.status === "INSUFFICIENT_LIQUIDITY" || stepT.status === "TARGET_UNAVAILABLE"
          ? "Hypothesis barrier: no zero-capital route to 300 BTC proven. Continue discovery; do not fake ledger."
          : "Continue honest discovery / simulation. Mainnet closed.",
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));

  const okStatuses = new Set(["READY_FOR_OWNER", "REAL_SETTLEMENT_CONFIRMED", "ROUTE_FOUND"]);
  if (!okStatuses.has(stepT.status) || !gate.pass) {
    process.exitCode = 2;
  }
}

run().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e.message || String(e) }, null, 2));
  process.exit(1);
});
