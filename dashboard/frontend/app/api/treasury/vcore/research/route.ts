import { NextRequest, NextResponse } from "next/server";
import { STON_NATIVE_TON } from "../../../../lib/treasury/vcoreConversion";
import { emptyValueEngine } from "../../../../lib/treasury/vcoreValueEngine";
import {
  DEFAULT_HYPOTHESES,
  buildProvenance,
  defaultOpportunities,
  evaluateGenesisPass,
  evaluateKillSwitch,
  syncHypotheses,
  PERMISSIONLESS_SETTLEMENT_LAW,
  type AssetScanRow,
  type RealityLedgerSnapshot,
  type ValueProofReport,
} from "../../../../lib/treasury/vcoreResearch";
import { readGenesisState, readRuntimeJson, writeRuntimeJson } from "../../../../lib/treasury/vcoreRuntimePaths";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function ledgerFromGenesis(g: Record<string, unknown> | null): RealityLedgerSnapshot {
  const stored = readRuntimeJson<RealityLedgerSnapshot & { frozen?: boolean }>("vcore_reality_ledger.json");
  const supply = Number(g?.supplyHuman || 1_000_000);
  const base: RealityLedgerSnapshot & { frozen?: boolean; law?: string } = stored || {
    model: {
      usd: supply,
      note: "DECLARED/MODEL reference only — not cash.",
    },
    real: {
      ton: 0,
      btc: 0,
      note: "FROZEN at 0 until confirmed external TON/BTC receipt. Creating VCORE does NOT increase REAL.",
    },
    transactions: [],
    frozen: true,
  };
  base.model.usd = supply;
  // Hard law — Genesis never paints REAL
  base.real = {
    ton: 0,
    btc: 0,
    note: "FROZEN at 0. VCORE asset ≠ REAL TON/BTC. Unfreeze only after confirmed external receipt.",
  };
  base.frozen = true;
  writeRuntimeJson("vcore_reality_ledger.json", base);
  return base;
}

async function runValueProof(g: Record<string, unknown> | null): Promise<ValueProofReport> {
  const layers = emptyValueEngine(Number(g?.supplyHuman || 1_000_000));
  const master = (g?.jettonMaster as string) || null;

  if (!master) {
    return {
      at: new Date().toISOString(),
      layers,
      route: null,
      quote: null,
      fees: null,
      slippage: "0.01",
      expectedTon: null,
      simulation: "FAIL",
      blocker: "VCORE_NOT_DEPLOYED",
      message:
        "PROVE VALUE: нет Jetton master. DECLARED/MODEL остаются reference; EXECUTABLE/REALIZED = 0.",
    };
  }

  // Mainnet STON discovery — honest: testnet jetton won't list there
  try {
    const res = await fetch("https://api.ston.fi/v1/swap/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        offer_address: master,
        ask_address: STON_NATIVE_TON,
        units: String(BigInt(1_000_000) * 10n ** 9n),
        slippage_tolerance: "0.01",
      }),
      cache: "no-store",
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        at: new Date().toISOString(),
        layers,
        route: "VCORE → TON (STON.fi attempted)",
        quote: null,
        fees: null,
        slippage: "0.01",
        expectedTon: "0",
        simulation: "FAIL",
        blocker: "NO_ROUTE_OR_LIQUIDITY",
        message: `Route search failed HTTP ${res.status}. Model value unchanged. Executable=0.`,
      };
    }
    const out = json.ask_units ?? json.out_units ?? null;
    layers.executable.amount = out ? Number(out) / 1e9 : 0;
    layers.executable.note = "From STON simulate units (not REALIZED).";
    layers.hypothesis = layers.executable.amount > 0 ? "EXECUTABLE_PARTIAL" : "MODEL_ONLY";
    return {
      at: new Date().toISOString(),
      layers,
      route: "VCORE → TON",
      quote: out ? String(out) : null,
      fees: json.fee_units != null ? String(json.fee_units) : null,
      slippage: "0.01",
      expectedTon: out ? String(Number(out) / 1e9) : "0",
      simulation: "PASS",
      blocker: "NONE",
      message: "Simulation PASS — still not REALIZED until signed+confirmed tx.",
    };
  } catch (e) {
    return {
      at: new Date().toISOString(),
      layers,
      route: null,
      quote: null,
      fees: null,
      slippage: "0.01",
      expectedTon: "0",
      simulation: "FAIL",
      blocker: "SCAN_ERROR",
      message: e instanceof Error ? e.message : String(e),
    };
  }
}

async function runAssetScan(g: Record<string, unknown> | null): Promise<AssetScanRow[]> {
  const master = (g?.jettonMaster as string) || null;
  const rows: AssetScanRow[] = [
    {
      asset: "TON",
      network: "TON",
      vcoreRoute: master ? "VCORE→TON ?" : "need Genesis",
      liquidity: "unknown",
      status: master ? "UNKNOWN" : "NO_ROUTE",
      detail: "STON.fi native TON asset exists; VCORE pool not assumed.",
    },
    {
      asset: "USDT",
      network: "TON",
      vcoreRoute: "VCORE→USDT ?",
      liquidity: "unknown",
      status: "DISCOVERED",
      detail: "USDT jetton markets exist on TON DEXes; VCORE pair not verified.",
    },
    {
      asset: "BTC",
      network: "Bitcoin",
      vcoreRoute: "none (no bridge)",
      liquidity: "n/a",
      status: "BLOCKED",
      detail: "No autonomous bridge execute. Kill Switch.",
    },
    {
      asset: "Jettons",
      network: "TON",
      vcoreRoute: "scan catalogs",
      liquidity: "varies",
      status: "DISCOVERED",
      detail: "Catalog reachable via STON assets API; VCORE listing separate.",
    },
    {
      asset: "EVM tokens",
      network: "EVM",
      vcoreRoute: "none",
      liquidity: "n/a",
      status: "BLOCKED",
      detail: "Cross-chain not enabled for VCORE experiment.",
    },
  ];

  try {
    const ton = await fetch(`https://api.ston.fi/v1/assets/${STON_NATIVE_TON}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (ton.ok) {
      rows[0].status = master ? "UNKNOWN" : "DISCOVERED";
      rows[0].detail = "TON asset meta OK on STON.fi. VCORE route still unproven.";
      rows[0].liquidity = "TON markets live (not VCORE)";
    }
  } catch {
    rows[0].detail = "STON.fi unreachable during scan";
  }

  if (master) {
    rows[0].vcoreRoute = `VCORE(${master.slice(0, 8)}…)→TON`;
  }
  return rows;
}

/**
 * GET /api/treasury/vcore/research — full research snapshot
 * POST { action: prove|scan|provenance|verify|ledger|hypotheses|kill }
 */
export async function GET() {
  const g = readGenesisState();
  const genesisPass = evaluateGenesisPass(g);
  const provenance = buildProvenance(g);
  const ledger = ledgerFromGenesis(g);
  const layers = emptyValueEngine(Number(g?.supplyHuman || 1_000_000));
  const kill = evaluateKillSwitch({
    network: (g?.network as string) || "ton-testnet",
    jettonMaster: (g?.jettonMaster as string) || null,
    simulation: "FAIL",
    emergency: false,
  });
  const hypotheses = syncHypotheses(DEFAULT_HYPOTHESES, g, null);
  const opportunities = defaultOpportunities();

  return NextResponse.json({
    ok: true,
    at: new Date().toISOString(),
    supplyHuman: g?.supplyHuman || "1000000",
    genesis: {
      stage: g?.stage || "NOT_STARTED",
      status: g?.status || "GENESIS_DRAFT",
      jettonMaster: g?.jettonMaster || null,
      adminAddress: g?.adminAddress || null,
      blockers: g?.blockers || [],
    },
    genesisPass,
    layers,
    provenance,
    ledger,
    hypotheses,
    opportunities,
    killSwitch: kill,
    settlementLaw: PERMISSIONLESS_SETTLEMENT_LAW,
    gates: {
      lpAllowed: false,
      mainnetAllowed: false,
      researchExecutionOpen: false,
      nextAfterGenesisPass: "dex_discovery",
    },
    priority: [
      "Genesis Gate (Faucet→Verify+External)",
      "DEX Discovery (listed? pool? quote?)",
      "Executable simulation",
      "Permissionless settlement hunt (H5)",
      "Testnet Conversion only if route exists",
      "LP/mainnet later",
    ],
  });
}

export async function POST(req: NextRequest) {
  let body: { action?: string; emergency?: boolean };
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  const action = (body.action || "prove").toLowerCase();
  const g = readGenesisState();

  if (action === "prove") {
    const proof = await runValueProof(g);
    writeRuntimeJson("vcore_last_value_proof.json", proof);
    const hypotheses = syncHypotheses(DEFAULT_HYPOTHESES, g, proof);
    writeRuntimeJson("vcore_hypotheses.json", { at: proof.at, hypotheses });
    const kill = evaluateKillSwitch({
      network: (g?.network as string) || "ton-testnet",
      jettonMaster: (g?.jettonMaster as string) || null,
      simulation: proof.simulation,
      emergency: !!body.emergency,
    });
    return NextResponse.json({ ok: true, action: "prove", proof, hypotheses, killSwitch: kill });
  }

  if (action === "scan") {
    const assets = await runAssetScan(g);
    writeRuntimeJson("vcore_asset_scan.json", { at: new Date().toISOString(), assets });
    return NextResponse.json({ ok: true, action: "scan", assets });
  }

  if (action === "provenance" || action === "verify") {
    const certificate = buildProvenance(g);
    return NextResponse.json({
      ok: true,
      action: "verify",
      verified: certificate.verified,
      certificate,
      message: certificate.verified
        ? "VERIFY VCORE → VERIFIED"
        : `VERIFY VCORE → NOT VERIFIED (${certificate.blockers.join(", ")})`,
    });
  }

  if (action === "ledger") {
    return NextResponse.json({ ok: true, action: "ledger", ledger: ledgerFromGenesis(g) });
  }

  if (action === "hypotheses") {
    const last = readRuntimeJson<ValueProofReport>("vcore_last_value_proof.json");
    const hypotheses = syncHypotheses(DEFAULT_HYPOTHESES, g, last);
    return NextResponse.json({ ok: true, action: "hypotheses", hypotheses });
  }

  if (action === "kill") {
    const kill = evaluateKillSwitch({
      network: (g?.network as string) || "ton-testnet",
      jettonMaster: (g?.jettonMaster as string) || null,
      simulation: "FAIL",
      emergency: true,
    });
    return NextResponse.json({
      ok: true,
      action: "kill",
      killSwitch: kill,
      message: "EMERGENCY STOP — no send allowed",
    });
  }

  if (action === "opportunities") {
    return NextResponse.json({ ok: true, action: "opportunities", opportunities: defaultOpportunities() });
  }

  return NextResponse.json({ ok: false, error: "unknown action" }, { status: 400 });
}
