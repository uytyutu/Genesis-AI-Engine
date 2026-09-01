import { NextRequest, NextResponse } from "next/server";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { readGenesisState, runtimeCandidates } from "../../../../lib/treasury/vcoreRuntimePaths";
import { evaluateGenesisPass } from "../../../../lib/treasury/vcoreResearch";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function readPipelineLast() {
  for (const p of runtimeCandidates("vcore_pipeline_last.json")) {
    try {
      if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, "utf8"));
    } catch {
      /* next */
    }
  }
  return null;
}

function repoRoot(): string {
  const cwd = process.cwd();
  const candidates = [cwd, path.join(cwd, "..", ".."), path.join(cwd, "..")];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "scripts", "vcorePipelineMaster.js"))) return c;
  }
  return path.join(cwd, "..", "..");
}

/**
 * GET — last pipeline report + genesis gate
 * POST { action: "dry-run", amount?: string } — runs honest pipeline (no broadcast)
 */
export async function GET() {
  const g = readGenesisState();
  const pass = evaluateGenesisPass(g);
  return NextResponse.json({
    ok: true,
    genesisPass: pass,
    stage: g?.stage || "NOT_STARTED",
    target: { asset: "BTC", amount: 300, maxCapitalEur: 0 },
    realSettlementPainted: false,
    mainnetExecution: false,
    law: "PERMISSIONLESS_SETTLEMENT_LAW — never paint 300 BTC; UTXO proof only",
    last: readPipelineLast(),
    settlementStatus: readPipelineLast()?.settlementStatus || null,
    cli: "npm run vcore:pipeline",
    contour:
      "Genesis → DEX discover/simulate → Target Settlement Engine (300 BTC / €0) → BTC only after chain confirm",
  });
}

export async function POST(req: NextRequest) {
  let body: { action?: string; amount?: string };
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  if (body.action !== "dry-run" && body.action !== "run") {
    return NextResponse.json({ ok: false, error: "use action=dry-run" }, { status: 400 });
  }

  const root = repoRoot();
  const amount = String(body.amount || "1000");
  const r = spawnSync(
    process.execPath,
    [path.join(root, "scripts", "vcorePipelineMaster.js"), "--amount", amount],
    { cwd: root, encoding: "utf8", timeout: 90_000 },
  );

  const last = readPipelineLast();
  return NextResponse.json({
    ok: r.status === 0 || r.status === 2,
    exitCode: r.status,
    stderr: (r.stderr || "").slice(0, 500),
    last,
    realSettlement: false,
    note: "exit 2 = honest STOP (no route / genesis incomplete). Not a crash.",
  });
}
