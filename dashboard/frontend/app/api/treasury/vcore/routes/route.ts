import { NextRequest, NextResponse } from "next/server";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { runtimeCandidates, readGenesisState } from "../../../../lib/treasury/vcoreRuntimePaths";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function readLast() {
  for (const p of runtimeCandidates("vcore_routes_last.json")) {
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
  for (const c of [cwd, path.join(cwd, "..", ".."), path.join(cwd, "..")]) {
    if (fs.existsSync(path.join(c, "scripts", "vcoreRouteFinder.js"))) return c;
  }
  return path.join(cwd, "..", "..");
}

export async function GET() {
  const g = readGenesisState();
  return NextResponse.json({
    ok: true,
    genesisStage: g?.stage || "NOT_STARTED",
    jettonMaster: g?.jettonMaster || null,
    last: readLast(),
    cli: "npm run vcore:routes",
    wallets: {
      metamask: "EVM / ETH treasury only — cannot sign TON Jetton swaps",
      ton: "Tonkeeper / TON Connect required for VCORE→TON",
    },
  });
}

export async function POST(req: NextRequest) {
  let body: { amount?: string };
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  const root = repoRoot();
  const amount = String(body.amount || "1000000");
  const r = spawnSync(
    process.execPath,
    [path.join(root, "scripts", "vcoreRouteFinder.js"), "--amount", amount],
    { cwd: root, encoding: "utf8", timeout: 90_000 },
  );
  return NextResponse.json({
    ok: true,
    exitCode: r.status,
    stderr: (r.stderr || "").slice(0, 400),
    report: readLast(),
    realSettlement: false,
    broadcast: false,
  });
}
