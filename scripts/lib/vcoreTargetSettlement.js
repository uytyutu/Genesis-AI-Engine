/**
 * Target Settlement Engine — honest capacity vs ambition.
 *
 * TARGET: 300 BTC · MAX CAPITAL: 0
 * Creating 1e6 VCORE does NOT create a claim on 300 BTC.
 * If liquidity is 0.0001 BTC, report 0.0001 — never paint 300.
 * REAL_SETTLEMENT_CONFIRMED only after Bitcoin network confirmation of UTXOs.
 * No mainnet execution in this brick.
 */
"use strict";

const DEFAULT_TARGET = {
  asset: "BTC",
  amount: 300, // aspirational ceiling for gap math — never painted as balance
  maxCapitalEur: 0,
  mode: "MAXIMUM_REALIZED_BTC",
  networkExecution: "testnet_path_only",
  mainnetExecution: false,
  note: "Report actual realized BTC under capital €0. Do not promise 300.",
};

/**
 * @typedef {'TARGET_UNAVAILABLE'|'INSUFFICIENT_LIQUIDITY'|'CAPITAL_REQUIRED'|'ROUTE_FOUND'|'SIMULATION_FAILED'|'READY_FOR_OWNER'|'REAL_SETTLEMENT_CONFIRMED'|'WAITING_GENESIS'|'IDENTITY_FAIL'} SettlementStatus
 */

function num(x, d = 0) {
  const n = Number(x);
  return Number.isFinite(n) ? n : d;
}

/**
 * Evaluate whether discovered route can meet TARGET under MAX CAPITAL = 0.
 *
 * @param {object} input
 * @param {object} input.genesisGate
 * @param {object|null} input.dexResult — from executeVcoreToTonSwap
 * @param {object|null} input.bridgeResult — from bridgeTonToBtc
 * @param {object} input.ledger
 * @param {{asset?:string,amount?:number,maxCapitalEur?:number}|null} input.target
 * @param {string|null} input.vcoreAvailable — human units
 */
function evaluateTargetSettlement(input) {
  const target = {
    ...DEFAULT_TARGET,
    ...(input.target || {}),
  };
  const vcoreAvailable = num(input.vcoreAvailable, 0);
  const gate = input.genesisGate || {};
  const dex = input.dexResult || {};
  const bridge = input.bridgeResult || {};
  const ledger = input.ledger || { real: { ton: 0, btc: 0 } };
  const realBtc = num(ledger.real?.btc, 0);
  const realTon = num(ledger.real?.ton, 0);

  const discovery = {
    targetAsset: target.asset,
    targetAmount: target.amount,
    maxCapitalEur: target.maxCapitalEur,
    vcoreAvailable,
    routeFound: false,
    liquidityBtc: 0,
    requiredCapitalEur: null,
    gasEur: null,
    fees: null,
    priceImpact: null,
    expectedBtc: 0,
    gapToTargetBtc: target.amount,
  };

  /** Already have verified BTC UTXOs counted in Reality Ledger */
  if (realBtc >= target.amount) {
    return finalize({
      status: "REAL_SETTLEMENT_CONFIRMED",
      discovery: {
        ...discovery,
        expectedBtc: realBtc,
        liquidityBtc: realBtc,
        gapToTargetBtc: 0,
        routeFound: true,
      },
      message: `Reality Ledger already shows ≥ ${target.amount} BTC — must still be Bitcoin UTXO-verified externally.`,
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: true,
      evidenceRequired: ["bitcoin_txids", "utxo_set_match", "external_confirm"],
    });
  }

  if (!gate.pass) {
    return finalize({
      status: "WAITING_GENESIS",
      discovery,
      message:
        "Genesis Gate not PASS. Cannot claim route to 300 BTC. Faucet → deploy → transfer → verify + EXTERNAL first.",
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  const listed = !!dex.discovery?.listed || dex.simulation?.simulation === "PASS";
  const simPass = dex.simulation?.simulation === "PASS";
  const simFail =
    dex.simulation?.simulation === "FAIL" ||
    dex.status === "NO_EXECUTABLE_ROUTE" ||
    dex.blocker === "WAITING_GENESIS";

  // Honest BTC expectation from VCORE→TON path alone is UNKNOWN without TON/BTC market + size.
  // We never invent 300 BTC from MODEL.
  let expectedBtcFromQuote = 0;
  if (simPass && dex.simulation?.expectedTon) {
    // Without a live TON→BTC depth quote, executable BTC toward target = 0 (unknown ≠ target).
    // Optional hint only: do not promote to expectedBtc for TARGET fill.
    discovery.fees = dex.simulation.fees;
    discovery.tonLegExpected = dex.simulation.expectedTon;
  }

  // Bridge / liquidity toward BTC
  if (bridge.status === "BLOCKED_UNTIL_REAL_TON" || realTon <= 0) {
    discovery.liquidityBtc = 0;
    discovery.expectedBtc = 0;
  }

  // Capital law: MAX CAPITAL = 0 → any required buy of VCORE/TON/LP funding = CAPITAL_REQUIRED
  const capitalNeededToCreateLiquidity = 0; // self-mint path; LP funding would be >0
  // If route needs us to seed LP or buy into pool → capital > 0
  const wouldNeedLpOrBuy = !listed || !simPass;
  // Zero-capital hypothesis: we do not count "seeding 300 BTC of liquidity ourselves"
  if (wouldNeedLpOrBuy === false && simPass) {
    discovery.routeFound = true;
    discovery.requiredCapitalEur = 0;
  } else {
    discovery.routeFound = listed && simPass;
    discovery.requiredCapitalEur = discovery.routeFound ? 0 : null;
  }

  // Capacity vs target — without a BTC depth quote, liquidity toward 300 = 0
  discovery.liquidityBtc = Math.min(discovery.liquidityBtc, expectedBtcFromQuote);
  discovery.expectedBtc = Math.min(discovery.liquidityBtc, target.amount);
  discovery.gapToTargetBtc = Math.max(0, target.amount - discovery.expectedBtc);
  discovery.priceImpact = discovery.expectedBtc > 0 ? "unknown_until_btc_leg_quote" : "n/a";
  discovery.gasEur = 0;
  discovery.requiredCapitalEur = target.maxCapitalEur;

  if (!listed && !simPass) {
    return finalize({
      status: "TARGET_UNAVAILABLE",
      discovery: { ...discovery, routeFound: false },
      message:
        "No voluntary VCORE→…→BTC route discovered. Minting VCORE does not create a claim on 300 BTC.",
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  if (simFail || (!simPass && listed)) {
    return finalize({
      status: "SIMULATION_FAILED",
      discovery: { ...discovery, routeFound: !!listed },
      message: "Asset may be visible but simulate did not yield executable output toward BTC target.",
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  if (simPass && discovery.expectedBtc <= 0) {
    return finalize({
      status: "INSUFFICIENT_LIQUIDITY",
      discovery: {
        ...discovery,
        routeFound: true,
        liquidityBtc: 0,
        expectedBtc: 0,
        gapToTargetBtc: target.amount,
      },
      message: `Route/sim may exist on a leg, but proven BTC liquidity toward target is 0 (not ${target.amount}). Do not display ${target.amount} BTC.`,
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  if (discovery.expectedBtc > 0 && discovery.expectedBtc < target.amount) {
    return finalize({
      status: "INSUFFICIENT_LIQUIDITY",
      discovery,
      message: `Executable BTC ${discovery.expectedBtc} < target ${target.amount}. Report actual capacity only.`,
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  // Capital: if maxCapital is 0 but filling target requires buying liquidity / seeding
  if (target.maxCapitalEur === 0 && discovery.requiredCapitalEur > 0) {
    return finalize({
      status: "CAPITAL_REQUIRED",
      discovery,
      message: "Target fill needs capital > 0; zero-capital hypothesis fails for this route.",
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  if (discovery.routeFound && discovery.expectedBtc >= target.amount && simPass) {
    return finalize({
      status: "READY_FOR_OWNER",
      discovery,
      message:
        "Hypothetical full path meets target on paper — OWNER APPROVAL required. No auto broadcast. Mainnet execution closed.",
      ownerApprovalRequired: true,
      mainnetExecution: false,
      realSettlement: false,
      gatesRemaining: [
        "IDENTITY",
        "LIQUIDITY",
        "QUOTE",
        "SIMULATION",
        "RISK_CHECK",
        "OWNER_APPROVAL",
        "SIGN",
        "BROADCAST",
        "BITCOIN_CONFIRMATION",
        "300_BTC_VERIFIED",
      ],
    });
  }

  if (discovery.routeFound) {
    return finalize({
      status: "ROUTE_FOUND",
      discovery,
      message: "Partial route found — not enough for TARGET; continue discovery.",
      ownerApprovalRequired: false,
      mainnetExecution: false,
      realSettlement: false,
    });
  }

  return finalize({
    status: "TARGET_UNAVAILABLE",
    discovery,
    message: "No qualifying zero-capital route to target BTC.",
    ownerApprovalRequired: false,
    mainnetExecution: false,
    realSettlement: false,
  });
}

function finalize( partial) {
  return {
    engine: "TargetSettlementEngine",
    target: {
      asset: DEFAULT_TARGET.asset,
      amount: DEFAULT_TARGET.amount,
      maxCapitalEur: DEFAULT_TARGET.maxCapitalEur,
    },
    status: partial.status,
    discovery: partial.discovery,
    message: partial.message,
    ownerApprovalRequired: !!partial.ownerApprovalRequired,
    mainnetExecution: false,
    realSettlement: !!partial.realSettlement,
    law: "Never paint TARGET amount. Evidence = Bitcoin UTXOs / txids only.",
    gatesRemaining: partial.gatesRemaining || null,
    evidenceRequired: partial.evidenceRequired || null,
    at: new Date().toISOString(),
  };
}

module.exports = {
  DEFAULT_TARGET,
  evaluateTargetSettlement,
};
