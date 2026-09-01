/**
 * TON → BTC non-custodial bridge adapter (honest).
 *
 * Blocked until REAL TON exists from confirmed settlement.
 * Does NOT call random KYC-free deposit APIs by default (Owner must name provider).
 * Never paints Reality Ledger REAL BTC without External Payout / tx evidence.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const LEDGER_PATH = path.join(ROOT, ".runtime", "vcore_reality_ledger.json");

function readLedger() {
  try {
    if (fs.existsSync(LEDGER_PATH)) return JSON.parse(fs.readFileSync(LEDGER_PATH, "utf8"));
  } catch {
    /* empty */
  }
  return {
    real: { ton: 0, btc: 0 },
    frozen: true,
    transactions: [],
  };
}

/**
 * @param {{ tonAmount: string, destinationBtcAddress: string, provider?: string, force?: boolean }} opts
 */
async function bridgeTonToBtc(opts) {
  const tonAmount = String(opts.tonAmount || "0");
  const destinationBtcAddress = String(opts.destinationBtcAddress || "").trim();
  const provider = (opts.provider || "").trim();
  const ledger = readLedger();
  const realTon = Number(ledger.real?.ton || 0);

  if (!destinationBtcAddress) {
    return {
      ok: false,
      status: "BLOCKED",
      blocker: "NO_BTC_DESTINATION",
      realSettlement: false,
      message: "Provide destination BTC address (own wallet only).",
    };
  }

  if (realTon <= 0 && !opts.force) {
    return {
      ok: false,
      status: "BLOCKED_UNTIL_REAL_TON",
      blocker: "REAL_TON_ZERO",
      realTon,
      realSettlement: false,
      message:
        "Reality Ledger REAL TON = 0 (frozen through Genesis). Bridge cannot invent BTC. First need confirmed VCORE→TON settlement.",
    };
  }

  const amount = Number(tonAmount);
  if (!Number.isFinite(amount) || amount <= 0) {
    return {
      ok: false,
      status: "BLOCKED",
      blocker: "INVALID_TON_AMOUNT",
      realSettlement: false,
      message: "Invalid TON amount",
    };
  }

  if (!provider) {
    return {
      ok: true,
      status: "ADAPTER_READY_NO_PROVIDER",
      blocker: "PROVIDER_NOT_SELECTED",
      realSettlement: false,
      depositAddress: null,
      expectedBtc: null,
      message:
        "Non-custodial bridge interface ready. Owner must name audited provider (no auto coinoswap). Until then: research only.",
      destinationBtcAddress,
      tonAmount,
    };
  }

  // Explicit: we do not auto-POST to unverified third-party swap APIs in this brick.
  return {
    ok: false,
    status: "PROVIDER_CALL_DISABLED",
    blocker: "NO_UNVERIFIED_BRIDGE_AUTOCALL",
    realSettlement: false,
    message: `Provider "${provider}" recorded as intent only. Live HTTP bridge call disabled until Owner security review + REAL TON > 0 + HITL confirm.`,
    destinationBtcAddress,
    tonAmount,
    provider,
  };
}

module.exports = {
  bridgeTonToBtc,
  readLedger,
};
