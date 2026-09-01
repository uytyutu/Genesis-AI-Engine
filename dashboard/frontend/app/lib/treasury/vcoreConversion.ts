/**
 * VCORE Conversion Engine — honest TON Jetton → DEX pipeline.
 * REAL SETTLEMENT only after on-chain confirmation.
 * VCORE without liquidity cannot mint TON.
 */

export type ConversionStage =
  | "IDENTITY"
  | "WALLET"
  | "DEX_DISCOVERY"
  | "QUOTE"
  | "SIMULATION"
  | "SIGN"
  | "BROADCAST"
  | "CONFIRM"
  | "REAL_SETTLEMENT";

export type ConversionBlocker =
  | "VCORE_NOT_DEPLOYED"
  | "NO_JETTON_MASTER"
  | "NO_POOL"
  | "ZERO_LIQUIDITY"
  | "ROUTE_MISSING"
  | "SIMULATION_FAIL"
  | "WALLET_NOT_CONNECTED"
  | "NETWORK_MISMATCH"
  | "NONE";

export interface VcoreIdentity {
  symbol: string;
  network: "ton-mainnet" | "ton-testnet" | "none";
  jettonMaster: string | null;
  decimals: number;
  status: "GENESIS_DRAFT" | "DEPLOYED_TESTNET" | "DEPLOYED_MAINNET" | "UNKNOWN";
  note: string;
}

export interface DexDiscoveryResult {
  venue: string;
  apiOk: boolean;
  routers: number;
  vcoreFound: boolean;
  tonAssetAddress: string | null;
  vcoreAssetAddress: string | null;
  poolFound: boolean;
  detail: string;
  rawError?: string;
}

export interface ConversionQuote {
  from: string;
  to: string;
  amountIn: string;
  amountOut: string | null;
  minReceive: string | null;
  feeHint: string | null;
  priceImpact: string | null;
  simulation: "PASS" | "FAIL" | "SKIPPED";
  blocker: ConversionBlocker;
  message: string;
}

export interface ConversionPipelineState {
  stages: Record<ConversionStage, "pending" | "pass" | "fail" | "skip">;
  identity: VcoreIdentity;
  discovery: DexDiscoveryResult | null;
  quote: ConversionQuote | null;
  walletConnected: boolean;
  tonBalanceConfirmed: string | null;
  realSettlement: boolean;
  farmNote: string;
}

/** Canonical native TON placeholder used by STON.fi (kind=Ton). */
export const STON_NATIVE_TON = "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c";

export const DEFAULT_VCORE_IDENTITY: VcoreIdentity = {
  symbol: "VCORE",
  network: "none",
  jettonMaster: null,
  decimals: 9,
  status: "GENESIS_DRAFT",
  note:
    "VCORE ещё не задеплоен как Jetton на TON. Без master-контракта и пула VCORE/TON обмен невозможен. Toloka ~20 € — Farm spend, не резерв DEX.",
};

export function emptyPipeline(identity: VcoreIdentity = DEFAULT_VCORE_IDENTITY): ConversionPipelineState {
  return {
    stages: {
      IDENTITY: identity.jettonMaster ? "pass" : "fail",
      WALLET: "pending",
      DEX_DISCOVERY: "pending",
      QUOTE: "pending",
      SIMULATION: "pending",
      SIGN: "skip",
      BROADCAST: "skip",
      CONFIRM: "skip",
      REAL_SETTLEMENT: "fail",
    },
    identity,
    discovery: null,
    quote: null,
    walletConnected: false,
    tonBalanceConfirmed: null,
    realSettlement: false,
    farmNote:
      "Virtus Toloka / API баланс (~20 €) — это Spend/операционный депозит Farm, не ликвидность VCORE/TON pool.",
  };
}
