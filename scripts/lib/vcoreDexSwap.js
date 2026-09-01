/**
 * VCORE → TON DEX path (honest).
 * PERMISSIONLESS_SETTLEMENT_LAW:
 *  - discover + simulate only until Owner opens broadcast
 *  - NEVER return REAL_SETTLEMENT without on-chain confirm
 *  - no pool / no route ⇒ FAIL (not painted TON)
 */
"use strict";

const { loadState } = require("./vcoreGenesisCore");

const STON = "https://api.ston.fi";
const STON_NATIVE_TON = "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c";

async function stonGet(path, ms = 20_000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(`${STON}${path}`, {
      signal: ctrl.signal,
      headers: { Accept: "application/json", "User-Agent": "VirtusCore-VCORE-DEX/0.1" },
    });
    const json = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, json };
  } finally {
    clearTimeout(t);
  }
}

async function stonPost(path, body, ms = 25_000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(`${STON}${path}`, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "User-Agent": "VirtusCore-VCORE-DEX/0.1",
      },
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, json };
  } finally {
    clearTimeout(t);
  }
}

/**
 * Discover whether VCORE appears in STON markets / assets (permissionless listing check).
 */
async function discoverVcoreRoute(jettonMaster) {
  const routers = await stonGet("/v1/routers");
  const routerList =
    (routers.json && routers.json.router_list) ||
    (Array.isArray(routers.json) ? routers.json : []);

  if (!jettonMaster) {
    return {
      ok: true,
      listed: false,
      routers: Array.isArray(routerList) ? routerList.length : 0,
      route: null,
      blocker: "NO_JETTON_MASTER",
      detail: "Genesis not deployed — cannot discover VCORE route.",
    };
  }

  const asset = await stonGet(`/v1/assets/${encodeURIComponent(jettonMaster)}`);
  const found = asset.ok && asset.json && (asset.json.asset || asset.json.contract_address);

  return {
    ok: true,
    listed: !!found,
    routers: Array.isArray(routerList) ? routerList.length : 0,
    route: found ? "VCORE → TON (candidate)" : null,
    assetMeta: found ? asset.json.asset || asset.json : null,
    blocker: found ? "NONE" : "VCORE_NOT_LISTED",
    detail: found
      ? "Asset meta found on STON.fi — still need pool + simulate PASS."
      : "STON.fi does not know this Jetton master. No voluntary route yet.",
  };
}

/**
 * Simulate VCORE → TON. Does NOT broadcast. Does NOT paint REAL.
 */
async function simulateVcoreToTon({ jettonMaster, amountHuman = "1000", decimals = 9 }) {
  if (!jettonMaster) {
    return {
      ok: true,
      simulation: "FAIL",
      blocker: "NO_JETTON_MASTER",
      expectedTon: null,
      fees: null,
      minReceive: null,
      executeAllowed: false,
      realSettlement: false,
      message: "No master — simulate skipped.",
    };
  }

  const n = Number(amountHuman);
  if (!Number.isFinite(n) || n <= 0) {
    return {
      ok: false,
      simulation: "FAIL",
      blocker: "INVALID_AMOUNT",
      executeAllowed: false,
      realSettlement: false,
      message: "Invalid amount",
    };
  }

  let scale = 1n;
  for (let i = 0; i < decimals; i++) scale *= 10n;
  const units = String(BigInt(Math.floor(n)) * scale);

  const sim = await stonPost("/v1/swap/simulate", {
    offer_address: jettonMaster,
    ask_address: STON_NATIVE_TON,
    units,
    slippage_tolerance: "0.01",
  });

  if (!sim.ok) {
    return {
      ok: true,
      simulation: "FAIL",
      blocker: "NO_ROUTE_OR_LIQUIDITY",
      expectedTon: null,
      fees: null,
      minReceive: null,
      executeAllowed: false,
      realSettlement: false,
      httpStatus: sim.status,
      raw: sim.json,
      message: `STON simulate HTTP ${sim.status} — no executable TON. REAL unchanged.`,
    };
  }

  const out = sim.json?.ask_units ?? sim.json?.out_units ?? null;
  const expectedTon = out != null ? String(Number(out) / 1e9) : null;

  return {
    ok: true,
    simulation: "PASS",
    blocker: "NONE",
    expectedTon,
    fees: sim.json?.fee_units != null ? String(sim.json.fee_units) : null,
    minReceive: sim.json?.min_ask_units ?? sim.json?.recommended_min_ask_units ?? null,
    slippage: "0.01",
    executeAllowed: false, // broadcast = separate Owner gate (not this brick)
    realSettlement: false,
    message:
      "Simulation PASS only. Broadcast + confirm required before any REAL TON. Pipeline will not paint settlement.",
    raw: sim.json,
  };
}

/**
 * Public entry: discover + simulate from local Genesis state.
 * broadcast=true is REJECTED here (Kill Switch / Owner later).
 */
async function executeVcoreToTonSwap({ amountHuman = "1000", broadcast = false } = {}) {
  const state = loadState();
  const jettonMaster = state.jettonMaster || null;

  if (broadcast) {
    return {
      ok: false,
      status: "KILL_SWITCH",
      realSettlement: false,
      blocker: "BROADCAST_FORBIDDEN_UNTIL_OWNER_GATE",
      message:
        "Broadcast disabled. PERMISSIONLESS_SETTLEMENT_LAW: no swap send until Genesis PASS + sim PASS + Owner open. Fake REAL_SETTLEMENT forbidden.",
    };
  }

  const discovery = await discoverVcoreRoute(jettonMaster);
  const simulation = await simulateVcoreToTon({
    jettonMaster,
    amountHuman,
    decimals: state.decimals || 9,
  });

  return {
    ok: true,
    status:
      simulation.simulation === "PASS"
        ? "SIMULATION_PASS_NOT_SETTLED"
        : "NO_EXECUTABLE_ROUTE",
    networkHint: "ston.fi API (listing/simulate) — not a painted balance",
    walletAddress: state.adminAddress,
    jettonMaster,
    vcoreBalanceHint: state.adminBalanceOnChain,
    discovery,
    simulation,
    realSettlement: false,
    receivedAsset: null,
    amount: null,
    law: "REAL only after confirmed on-chain TON receipt — never from this function alone.",
  };
}

module.exports = {
  STON_NATIVE_TON,
  discoverVcoreRoute,
  simulateVcoreToTon,
  executeVcoreToTonSwap,
};
