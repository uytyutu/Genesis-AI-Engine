/**
 * VCORE Route Finder v1 — honest graph discovery.
 * Versions: A Jetton→TON · B multi-hop · C →supported→BTC (THORChain)
 * ZERO-CAPITAL MODE classification. Never fabricate quote/balance. Never auto-broadcast.
 */
"use strict";

const { loadState } = require("./vcoreGenesisCore");
const { discoverVcoreRoute, simulateVcoreToTon, STON_NATIVE_TON } = require("./vcoreDexSwap");
const { DEFAULT_TARGET } = require("./vcoreTargetSettlement");

const STON = "https://api.ston.fi";
const THOR_POOLS = "https://thornode.ninerealms.com/thorchain/pools";

/** Major TON-side hop candidates (symbols / known roles — not assumed paired with VCORE). */
const HOP_CANDIDATES = [
  { id: "TON", role: "native", address: STON_NATIVE_TON },
  { id: "USDT", role: "stable", address: null },
  { id: "jUSDT", role: "stable_hint", address: null },
  { id: "NOT", role: "major_jetton_hint", address: null },
];

async function fetchJson(url, ms = 20_000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { Accept: "application/json", "User-Agent": "VirtusCore-RouteFinder/0.1" },
    });
    const json = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: null, error: e instanceof Error ? e.message : String(e) };
  } finally {
    clearTimeout(t);
  }
}

function classifyRoute({
  poolExists,
  listed,
  simPass,
  expectedOut,
  capitalRequiredEur,
  liquidityRequired,
  thorSupported,
  targetAsset,
}) {
  if (!listed && !poolExists) return "NO_ROUTE";
  if (listed && !simPass && !poolExists) return "UNSUPPORTED";
  if (!simPass) return "SIMULATION_FAILED";
  if (liquidityRequired) return "LIQUIDITY_REQUIRED";
  if (capitalRequiredEur > 0) return "CAPITAL_REQUIRED";
  if (targetAsset === "BTC" && !thorSupported && expectedOut <= 0) return "UNSUPPORTED";
  if (simPass && capitalRequiredEur === 0 && expectedOut > 0) {
    return expectedOut > 0 ? "ZERO_CAPITAL_EXECUTABLE" : "UNPROFITABLE";
  }
  if (simPass && capitalRequiredEur === 0 && expectedOut === 0) return "LIQUIDITY_REQUIRED";
  if (simPass) return "PROFITABLE";
  return "NO_ROUTE";
}

function zeroCapitalPass(route) {
  return (
    route.classification === "ZERO_CAPITAL_EXECUTABLE" &&
    route.capitalRequiredEur === 0 &&
    route.liquidityRequired === false &&
    route.protocolPermission === true &&
    route.externalBuyer === false &&
    (route.expectedTon > 0 || route.expectedBtc > 0)
  );
}

/**
 * Find routes VCORE → TON / USDT / BTC (via supported hops). Honest negatives.
 */
async function findVcoreRoutes({ amountHuman = "1000000", targetBtc = DEFAULT_TARGET.amount } = {}) {
  const state = loadState();
  const master = state.jettonMaster || null;
  const at = new Date().toISOString();

  const base = {
    at,
    engine: "VCORE_ROUTE_FINDER_v1",
    input: {
      vcore: master,
      amountHuman,
      supplyHuman: state.supplyHuman || "1000000",
      stage: state.stage,
      targets: ["TON", "BTC", "USDT", "major_TON_Jettons"],
      targetBtc,
      maxCapitalEur: 0,
    },
    architecture: {
      A: "VCORE → VCORE/TON pool → DEX → TON (needs both sides for LP if we seed)",
      B: "VCORE → X → TON (multi-hop; first hop needs liquidity)",
      C: "VCORE → supported asset → THORChain → BTC (VCORE not natively on THOR)",
    },
    analysisNote:
      "New Jetton without pool/liquidity cannot claim TON/BTC on honest DEX/THOR. DeDust: vault+pool+LP. THORChain: supported pools only.",
    routes: [],
    thor: null,
    ston: null,
    bestZeroCapital: null,
    towardTarget300Btc: null,
    broadcast: false,
    realSettlement: false,
  };

  if (!master) {
    base.routes.push({
      id: "A-direct-ton",
      path: ["VCORE", "TON"],
      version: "A",
      poolExists: false,
      listed: false,
      quote: null,
      fee: null,
      priceImpact: null,
      gas: null,
      supported: false,
      capitalRequiredEur: 0,
      liquidityRequired: true,
      externalBuyer: false,
      protocolPermission: false,
      expectedTon: 0,
      expectedBtc: 0,
      classification: "NO_ROUTE",
      zeroCapital: false,
      detail: "Genesis Jetton not deployed — discover blocked.",
    });
    base.towardTarget300Btc = {
      status: "WAITING_GENESIS",
      expectedBtc: 0,
      gap: targetBtc,
      message: "Cannot hunt 300 BTC until VCORE exists on-chain.",
    };
    return base;
  }

  const discovery = await discoverVcoreRoute(master);
  const simulation = await simulateVcoreToTon({
    jettonMaster: master,
    amountHuman,
    decimals: state.decimals || 9,
  });
  base.ston = { discovery, simulation };

  const listed = !!discovery.listed;
  const simPass = simulation.simulation === "PASS";
  const expectedTon = simPass && simulation.expectedTon ? Number(simulation.expectedTon) : 0;

  // Version A — direct VCORE → TON
  const routeA = {
    id: "A-direct-ton",
    path: ["VCORE", "TON"],
    version: "A",
    venue: "STON.fi (discover+simulate)",
    poolExists: simPass,
    listed,
    quote: simulation.expectedTon,
    fee: simulation.fees,
    priceImpact: simPass ? "from_sim" : null,
    gas: "ton_network_fee_separate",
    supported: listed || simPass,
    capitalRequiredEur: 0,
    liquidityRequired: !simPass,
    externalBuyer: false,
    protocolPermission: true,
    expectedTon,
    expectedBtc: 0,
    classification: "NO_ROUTE",
    zeroCapital: false,
    detail: "",
  };
  if (!listed && !simPass) {
    routeA.classification = "NO_ROUTE";
    routeA.detail =
      "No VCORE listing/pool on STON. Creating VCORE ≠ LP. DeDust path would need vault+pool+both assets.";
    routeA.liquidityRequired = true;
  } else if (!simPass) {
    routeA.classification = "SIMULATION_FAILED";
    routeA.detail = simulation.message || "Simulate failed — no executable TON.";
    routeA.liquidityRequired = true;
  } else if (expectedTon <= 0) {
    routeA.classification = "LIQUIDITY_REQUIRED";
    routeA.detail = "Sim PASS shape but expected TON ≤ 0.";
  } else {
    routeA.classification = "ZERO_CAPITAL_EXECUTABLE";
    routeA.detail = "Executable TON quote without seeding LP in this call (liquidity already in pool).";
  }
  routeA.zeroCapital = zeroCapitalPass(routeA);
  base.routes.push(routeA);

  // Version B — multi-hop hints (no fabricated VCORE→X pools)
  for (const hop of HOP_CANDIDATES.filter((h) => h.id !== "TON")) {
    const routeB = {
      id: `B-via-${hop.id}`,
      path: ["VCORE", hop.id, "TON"],
      version: "B",
      venue: "multi-hop (DeDust/STON capable in general — VCORE leg unverified)",
      poolExists: false,
      listed: false,
      quote: null,
      fee: null,
      priceImpact: null,
      gas: null,
      supported: false,
      capitalRequiredEur: 0,
      liquidityRequired: true,
      externalBuyer: false,
      protocolPermission: true,
      expectedTon: 0,
      expectedBtc: 0,
      classification: "NO_ROUTE",
      zeroCapital: false,
      detail: `No verified VCORE→${hop.id} pool. Multi-hop only works if first hop has real liquidity.`,
    };
    base.routes.push(routeB);
  }

  // Version C — THORChain supported assets → BTC
  const thorRes = await fetchJson(THOR_POOLS);
  let thorAssets = [];
  let btcPool = null;
  let tonOnThor = null;
  if (thorRes.ok && Array.isArray(thorRes.json)) {
    thorAssets = thorRes.json
      .filter((p) => p && (p.status === "Available" || p.status === "available"))
      .map((p) => p.asset)
      .filter(Boolean);
    btcPool = thorRes.json.find((p) => String(p.asset || "").includes("BTC"));
    tonOnThor = thorRes.json.find((p) => /TON/i.test(String(p.asset || "")));
  }
  base.thor = {
    ok: thorRes.ok,
    status: thorRes.status,
    error: thorRes.error || null,
    availableCount: thorAssets.length,
    btcSupported: !!btcPool,
    tonSupported: !!tonOnThor,
    sampleAssets: thorAssets.slice(0, 12),
    vcoreOnThor: false,
    note: "Arbitrary VCORE is NOT a THORChain asset. Path must be VCORE→supported→BTC.",
  };

  const routeC = {
    id: "C-thor-btc",
    path: ["VCORE", "TON_or_USDT", "THORChain", "BTC"],
    version: "C",
    venue: "THORChain (after TON DEX leg)",
    poolExists: !!btcPool,
    listed: false,
    quote: null,
    fee: null,
    priceImpact: null,
    gas: null,
    supported: !!btcPool && expectedTon > 0,
    capitalRequiredEur: 0,
    liquidityRequired: expectedTon <= 0,
    externalBuyer: false,
    protocolPermission: !!btcPool,
    expectedTon: 0,
    expectedBtc: 0,
    classification: "UNSUPPORTED",
    zeroCapital: false,
    detail: "",
  };

  if (!btcPool) {
    routeC.classification = thorRes.ok ? "UNSUPPORTED" : "SIMULATION_FAILED";
    routeC.detail = thorRes.ok
      ? "BTC pool not found/available on THORNode response."
      : `THORNode unreachable: ${thorRes.error || thorRes.status}`;
  } else if (expectedTon <= 0) {
    routeC.classification = "LIQUIDITY_REQUIRED";
    routeC.detail =
      "BTC is supported on THORChain, but VCORE→TON leg has 0 executable TON — cannot feed cross-chain.";
    routeC.liquidityRequired = true;
  } else {
    // We have TON quote but NO fabricated TON→BTC depth for 300 BTC
    routeC.classification = "LIQUIDITY_REQUIRED";
    routeC.expectedTon = expectedTon;
    routeC.expectedBtc = 0;
    routeC.detail = `TON leg may yield ~${expectedTon} TON; TON→BTC quote not fabricated. Not assuming depth for ${targetBtc} BTC.`;
    routeC.liquidityRequired = true;
  }
  routeC.zeroCapital = zeroCapitalPass(routeC);
  base.routes.push(routeC);

  // Seeding own VCORE/TON pool = CAPITAL_REQUIRED route (honest)
  base.routes.push({
    id: "A-seed-lp-then-swap",
    path: ["VCORE", "seed_LP(VCORE+TON)", "TON"],
    version: "A",
    venue: "DeDust/STON LP then swap",
    poolExists: false,
    listed: false,
    quote: null,
    fee: null,
    priceImpact: null,
    gas: null,
    supported: true,
    capitalRequiredEur: 1,
    liquidityRequired: true,
    externalBuyer: false,
    protocolPermission: true,
    expectedTon: 0,
    expectedBtc: 0,
    classification: "CAPITAL_REQUIRED",
    zeroCapital: false,
    detail:
      "Technically high success if we provide BOTH assets to LP — fails ZERO-CAPITAL MODE (need TON side).",
  });

  const zc = base.routes.filter((r) => r.zeroCapital || r.classification === "ZERO_CAPITAL_EXECUTABLE");
  base.bestZeroCapital = zc.sort((a, b) => b.expectedTon - a.expectedTon)[0] || null;

  const expectedBtcBest = Math.max(0, ...base.routes.map((r) => Number(r.expectedBtc) || 0));
  base.towardTarget300Btc = {
    status:
      expectedBtcBest >= targetBtc
        ? "READY_FOR_OWNER"
        : expectedBtcBest > 0
          ? "INSUFFICIENT_LIQUIDITY"
          : listed || simPass
            ? "INSUFFICIENT_LIQUIDITY"
            : "TARGET_UNAVAILABLE",
    expectedBtc: expectedBtcBest,
    gap: Math.max(0, targetBtc - expectedBtcBest),
    message:
      expectedBtcBest >= targetBtc
        ? "Do not auto-broadcast — Owner gate."
        : expectedBtcBest > 0
          ? `Show ${expectedBtcBest} BTC capacity only — never paint ${targetBtc}.`
          : `No proven BTC output from VCORE. Probability of zero-capital ${targetBtc} BTC via vanilla DEX/THOR ≈ 0 without unknown voluntary mechanism.`,
  };

  return base;
}

module.exports = {
  findVcoreRoutes,
  classifyRoute,
  zeroCapitalPass,
};
