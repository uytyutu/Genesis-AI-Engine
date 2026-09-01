import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { emptyValueEngine } from "../../../../lib/treasury/vcoreValueEngine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function stateCandidates(): string[] {
  const cwd = process.cwd();
  return [
    path.join(cwd, ".runtime", "vcore_genesis_state.json"),
    path.join(cwd, "..", "..", ".runtime", "vcore_genesis_state.json"),
    path.join(cwd, "..", ".runtime", "vcore_genesis_state.json"),
  ];
}

function readGenesisState(): Record<string, unknown> | null {
  for (const p of stateCandidates()) {
    try {
      if (fs.existsSync(p)) {
        return JSON.parse(fs.readFileSync(p, "utf8")) as Record<string, unknown>;
      }
    } catch {
      /* try next */
    }
  }
  return null;
}

/**
 * GET /api/treasury/vcore/genesis
 * Read-only Genesis identity + Value layers (from local .runtime state).
 * Deploy/mint/transfer = CLI only (keys in .env.ton).
 */
export async function GET() {
  const state = readGenesisState();
  if (!state) {
    return NextResponse.json({
      ok: true,
      stage: "NOT_STARTED",
      status: "GENESIS_DRAFT",
      network: "ton-testnet",
      jettonMaster: null,
      blockers: ["NO_STATE"],
      valueLayers: emptyValueEngine(1_000_000),
      gates: { lpAllowed: false, mainnetAllowed: false },
      cli: {
        init: "npm run vcore:genesis:init",
        deploy: "npm run vcore:genesis:deploy",
        transfer: "npm run vcore:genesis:transfer",
        verify: "npm run vcore:genesis:verify",
      },
      detail:
        "Genesis ещё не запускался. CLI создаст testnet wallet → faucet → deploy Jetton → mint → transfer → verify. LP закрыт.",
    });
  }

  const supply = Number(state.supplyHuman || 1_000_000);
  const valueLayers = (state.valueLayers as object) || emptyValueEngine(supply);

  return NextResponse.json({
    ok: true,
    ...state,
    valueLayers,
    identityPass: !!(state.jettonMaster && state.totalSupplyOnChain),
    verified: state.stage === "VERIFIED",
    externalVerification: state.externalVerification || {
      status: "PENDING",
      identity: null,
      mismatches: [],
    },
    realLedgerFrozen: true,
    cli: {
      init: "npm run vcore:genesis:init",
      deploy: "npm run vcore:genesis:deploy",
      transfer: "npm run vcore:genesis:transfer",
      verify: "npm run vcore:genesis:verify",
    },
    focusNow: "Faucet → Deploy → Transfer → Verify. Everything else closed.",
    law: "DECLARED/MODEL ≠ REAL. VCORE mint ≠ REAL TON. EXTERNAL VERIFICATION required for IDENTITY VERIFIED.",
  });
}

/**
 * POST { action: "refresh" } — re-read state file (verify stays on CLI for keys).
 */
export async function POST(req: NextRequest) {
  let body: { action?: string };
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  if (body.action === "refresh" || !body.action) {
    return GET();
  }
  return NextResponse.json(
    {
      ok: false,
      error: "Only action=refresh on API. Deploy/mint/transfer require local CLI + .env.ton",
    },
    { status: 400 },
  );
}
