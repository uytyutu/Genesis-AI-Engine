/**
 * VCORE Research Lab — layers never mixed.
 * GENESIS PASS gate before LP. Kill Switch before any send.
 */

import { emptyValueEngine, type ValueEngineSnapshot } from "./vcoreValueEngine";

export type HypothesisId = "H1" | "H2" | "H3" | "H4" | "H5";

export type HypothesisStatus =
  | "TESTING"
  | "WAITING_GENESIS"
  | "NOT_TESTED"
  | "RESEARCH"
  | "PASS"
  | "FAIL"
  | "BLOCKED";

export interface HypothesisRecord {
  id: HypothesisId;
  title: string;
  status: HypothesisStatus;
  method: string;
  observation: string;
  blockchainEvidence: string[];
  result: string | null;
}

export interface GenesisPassChecklist {
  jettonMasterDeployed: boolean;
  contractAddressVerified: boolean;
  supplyReadFromChain: boolean;
  walletOwnsVcore: boolean;
  transferConfirmed: boolean;
  explorerLinksPresent: boolean;
  virtusReadsIndependently: boolean;
  externalIdentityVerified: boolean;
  realSettlementIsNo: boolean;
  allPass: boolean;
}

export interface ProvenanceCertificate {
  symbol: string;
  network: string;
  masterContract: string | null;
  genesisTx: string | null;
  mintEvidence: string | null;
  transferEvidence: string | null;
  treasuryAdmin: string | null;
  currentOwnerHint: string | null;
  supplyOnChain: string | null;
  verified: boolean;
  blockers: string[];
  chain: string[];
}

export interface AssetScanRow {
  asset: string;
  network: string;
  vcoreRoute: string;
  liquidity: string;
  status: "DISCOVERED" | "NO_ROUTE" | "UNKNOWN" | "BLOCKED";
  detail: string;
}

export interface ValueProofReport {
  at: string;
  layers: ValueEngineSnapshot;
  route: string | null;
  quote: string | null;
  fees: string | null;
  slippage: string | null;
  expectedTon: string | null;
  simulation: "PASS" | "FAIL" | "SKIPPED";
  blocker: string;
  message: string;
}

export interface RealityLedgerSnapshot {
  model: { usd: number; note: string };
  real: { ton: number; btc: number; note: string };
  transactions: Array<{
    id: string;
    kind: string;
    network: string;
    hash: string | null;
    amount: string | null;
    asset: string | null;
    confirmed: boolean;
    at: string;
    note: string;
  }>;
}

export interface KillSwitchState {
  armed: boolean;
  reasons: string[];
  allowSend: boolean;
}

export interface OpportunityRow {
  id: string;
  channel: string;
  capitalRequiredEur: number;
  gasRequiredEur: number;
  rewardHint: string;
  expectedNet: string;
  risk: string;
  status: "RESEARCH" | "SKIPPED" | "LIVE_CANDIDATE";
}

export const DEFAULT_HYPOTHESES: HypothesisRecord[] = [
  {
    id: "H1",
    title: "Can VCORE obtain real market value?",
    status: "TESTING",
    method: "Separate DECLARED/MODEL/MARKET/EXECUTABLE/REALIZED; never collapse.",
    observation: "MODEL may be >0 while REALIZED=0.",
    blockchainEvidence: [],
    result: null,
  },
  {
    id: "H2",
    title: "Can self-minted VCORE convert to TON without buying VCORE?",
    status: "WAITING_GENESIS",
    method:
      "Create Jetton ourselves → discover permissionless routes that voluntarily accept VCORE → quote → simulate → confirmed TX only. No purchase of VCORE required; liquidity/protocol rules required.",
    observation:
      "Blocked until Genesis. Sending unknown Jetton to a DEX without a pool ≠ TON.",
    blockchainEvidence: [],
    result: null,
  },
  {
    id: "H3",
    title: "Can conversion be discovered autonomously?",
    status: "NOT_TESTED",
    method: "Universal Asset Scanner + STON.fi discovery without hard-coded pool.",
    observation: "Scanner runs; routes may be empty.",
    blockchainEvidence: [],
    result: null,
  },
  {
    id: "H4",
    title: "Can VCORE interact with multiple networks?",
    status: "NOT_TESTED",
    method: "Scan TON / Bitcoin / EVM surfaces; no bridge execute until evidence.",
    observation: "Multi-network discovery only.",
    blockchainEvidence: [],
    result: null,
  },
  {
    id: "H5",
    title:
      "Can Virtus find a zero-capital external value source and receive a confirmed real asset (then optionally exit to BTC)?",
    status: "RESEARCH",
    method:
      "MISSION VH-1: REAL OPPORTUNITY VERIFICATION (9 questions) → owner-gated action → on-chain confirm → Reality Ledger + SUCCESS MEMORY. KPI = REAL_EXTERNAL_ASSETS (>0), not opportunity count.",
    observation:
      "REAL_EXTERNAL_ASSETS = 0 · evidence empty · EXECUTABLE_NOW gated by Genesis + full verification. Candidates ≠ executable.",
    blockchainEvidence: [],
    result: null,
  },
];

/** Research law — never implement fake autonomous swap confirmations. */
export const PERMISSIONLESS_SETTLEMENT_LAW = {
  allowed: [
    "Self-mint VCORE (Genesis Jetton)",
    "Discover routes that list/accept VCORE by protocol rules",
    "Quote + simulate + Kill Switch",
    "REAL only after on-chain confirm of received TON/BTC + External Payout ID / tx hash",
  ],
  forbidden: [
    "Paint REAL_SETTLEMENT_CONFIRMED without chain confirmation",
    "Assume any DEX pays TON for unknown Jetton",
    "Exploit / confuse identity / drain foreign liquidity illegally",
    "Collapse MODEL $1,000,000 into REAL TON",
  ],
  nextGateAfterGenesis: "dex_discovery_then_executable_quote",
} as const;

export function evaluateGenesisPass(g: Record<string, unknown> | null): GenesisPassChecklist {
  const master = !!(g?.jettonMaster);
  const supply = !!(g?.totalSupplyOnChain && String(g.totalSupplyOnChain) !== "0");
  const owns = !!(g?.adminBalanceOnChain && Number(g.adminBalanceOnChain) > 0);
  const transfer = !!(g?.probeBalanceOnChain && Number(g.probeBalanceOnChain) > 0);
  const explorer = !!(g?.explorer && (g.explorer as { master?: string }).master);
  const stageOk = g?.stage === "VERIFIED" || (master && supply && owns);
  const ext = g?.externalVerification as { identity?: string } | undefined;
  const externalOk = ext?.identity === "IDENTITY_VERIFIED";
  const checklist: GenesisPassChecklist = {
    jettonMasterDeployed: master,
    contractAddressVerified: master && explorer,
    supplyReadFromChain: supply,
    walletOwnsVcore: owns,
    transferConfirmed: transfer,
    explorerLinksPresent: explorer,
    virtusReadsIndependently: stageOk || (master && supply),
    externalIdentityVerified: externalOk,
    realSettlementIsNo: true, // VCORE mint must NEVER flip this
    allPass: false,
  };
  checklist.allPass =
    checklist.jettonMasterDeployed &&
    checklist.contractAddressVerified &&
    checklist.supplyReadFromChain &&
    checklist.walletOwnsVcore &&
    checklist.transferConfirmed &&
    checklist.explorerLinksPresent &&
    checklist.virtusReadsIndependently &&
    checklist.externalIdentityVerified &&
    checklist.realSettlementIsNo;
  return checklist;
}

export function buildProvenance(g: Record<string, unknown> | null): ProvenanceCertificate {
  const master = (g?.jettonMaster as string) || null;
  const blockers: string[] = [];
  if (!master) blockers.push("NO_MASTER");
  if (!g?.totalSupplyOnChain) blockers.push("NO_ONCHAIN_SUPPLY");
  if (!g?.adminBalanceOnChain) blockers.push("NO_ADMIN_BALANCE");
  if (!g?.probeBalanceOnChain || Number(g.probeBalanceOnChain) <= 0) blockers.push("NO_TRANSFER_PROOF");

  return {
    symbol: "VCORE",
    network: (g?.network as string) || "ton-testnet",
    masterContract: master,
    genesisTx: (g?.deployAt as string) || null,
    mintEvidence: g?.totalSupplyOnChain
      ? `supply_on_chain=${g.totalSupplyOnChain}`
      : null,
    transferEvidence: g?.probeBalanceOnChain
      ? `probe_balance=${g.probeBalanceOnChain} at ${g.transferAt || "?"}`
      : null,
    treasuryAdmin: (g?.adminAddress as string) || null,
    currentOwnerHint: (g?.adminAddress as string) || null,
    supplyOnChain: (g?.totalSupplyOnChain as string) || null,
    verified: blockers.length === 0 && g?.stage === "VERIFIED",
    blockers,
    chain: [
      "VCORE GENESIS",
      master ? `Master ${master}` : "Master — missing",
      g?.deployAt ? `Genesis/Deploy marker ${g.deployAt}` : "Genesis TX — pending",
      g?.totalSupplyOnChain ? `Mint evidence supply=${g.totalSupplyOnChain}` : "Mint — pending",
      g?.adminAddress ? `Treasury ${g.adminAddress}` : "Treasury — pending",
      g?.adminAddress ? `Current owner hint ${g.adminAddress}` : "Owner — pending",
    ],
  };
}

export function evaluateKillSwitch(input: {
  network?: string;
  jettonMaster?: string | null;
  simulation?: string;
  quoteStale?: boolean;
  unknownContract?: boolean;
  emergency?: boolean;
}): KillSwitchState {
  const reasons: string[] = [];
  if (input.emergency) reasons.push("EMERGENCY_STOP");
  if (input.network && input.network !== "ton-testnet" && input.network !== "testnet") {
    reasons.push("WRONG_NETWORK");
  }
  if (!input.jettonMaster) reasons.push("UNKNOWN_OR_MISSING_CONTRACT");
  if (input.unknownContract) reasons.push("UNKNOWN_CONTRACT");
  if (input.simulation && input.simulation !== "PASS") reasons.push("SIMULATION_FAILED");
  if (input.quoteStale) reasons.push("QUOTE_STALE");
  return {
    armed: reasons.length > 0,
    reasons,
    allowSend: reasons.length === 0,
  };
}

export function syncHypotheses(
  base: HypothesisRecord[],
  g: Record<string, unknown> | null,
  proof: ValueProofReport | null,
): HypothesisRecord[] {
  const pass = evaluateGenesisPass(g);
  return base.map((h) => {
    if (h.id === "H1") {
      return {
        ...h,
        status: "TESTING",
        observation: `MODEL=${(proof?.layers || emptyValueEngine()).model.amount} REALIZED=${(proof?.layers || emptyValueEngine()).realSettlement.amount}`,
        result: "MODEL and REALIZED kept separate — PASS for honesty rule",
      };
    }
    if (h.id === "H2") {
      if (!pass.jettonMasterDeployed) {
        return { ...h, status: "WAITING_GENESIS", observation: "No Jetton master yet", result: null };
      }
      if (proof?.simulation === "PASS" && (proof.expectedTon || "0") !== "0") {
        return {
          ...h,
          status: "TESTING",
          observation: `Executable quote ${proof.expectedTon}`,
          blockchainEvidence: proof.route ? [proof.route] : [],
          result: null,
        };
      }
      return {
        ...h,
        status: "TESTING",
        observation: "Genesis advancing; conversion still 0 without LP",
        blockchainEvidence: g?.jettonMaster ? [String(g.jettonMaster)] : [],
        result: null,
      };
    }
    if (h.id === "H3") {
      return {
        ...h,
        status: proof ? (proof.route ? "TESTING" : "NOT_TESTED") : "NOT_TESTED",
        observation: proof?.message || h.observation,
        result: proof?.simulation === "PASS" ? "Route discovered" : null,
      };
    }
    if (h.id === "H5") {
      const realized = (proof?.layers || emptyValueEngine()).realSettlement.amount;
      const n = Number(realized) || 0;
      return {
        ...h,
        status: n > 0 ? "TESTING" : "RESEARCH",
        observation: `VH-1 KPI REAL_EXTERNAL_ASSETS≈${n} · Genesis=${pass.allPass ? "PASS" : "FAIL"} · candidates≠EXECUTABLE_NOW`,
        blockchainEvidence: [],
        result: n > 0 ? "First real external asset recorded" : null,
      };
    }
    return h;
  });
}

export function defaultOpportunities(): OpportunityRow[] {
  return [
    {
      id: "opp-permissionless-settlement",
      channel:
        "Target Settlement: VCORE → up to 300 BTC · MAX CAPITAL €0 (discover only; no foreign UTXO)",
      capitalRequiredEur: 0,
      gasRequiredEur: 0,
      rewardHint: "Statuses: TARGET_UNAVAILABLE | INSUFFICIENT_LIQUIDITY | … | REAL only after BTC confirm",
      expectedNet: "Actual executable BTC only — never auto-fill 300",
      risk: "Economic barrier likely; painting 300 BTC falsifies experiment",
      status: "RESEARCH",
    },
    {
      id: "opp-ston-testnet",
      channel: "STON.fi / DEX discovery after Genesis (quote only until LP gate)",
      capitalRequiredEur: 0,
      gasRequiredEur: 0,
      rewardHint: "Executable quote if pool exists — still not REALIZED until TX",
      expectedNet: "0 until listed + liquidity",
      risk: "No pool ⇒ simulation FAIL (honest)",
      status: "RESEARCH",
    },
    {
      id: "opp-value-hunter",
      channel: "Legal bounty / Immunefi path (separate from Jetton mint)",
      capitalRequiredEur: 0,
      gasRequiredEur: 0,
      rewardHint: "External payout → Reality Ledger REAL",
      expectedNet: "Unknown until report accepted",
      risk: "Scope / duplicate / skill",
      status: "RESEARCH",
    },
    {
      id: "opp-fake-autonomous-swap",
      channel: "Autonomous swap stub that returns REAL_SETTLEMENT_CONFIRMED without chain",
      capitalRequiredEur: 0,
      gasRequiredEur: 0,
      rewardHint: "N/A",
      expectedNet: "Rejected by Kill Switch / Finance Reality Law",
      risk: "Would falsify the experiment",
      status: "SKIPPED",
    },
  ];
}
