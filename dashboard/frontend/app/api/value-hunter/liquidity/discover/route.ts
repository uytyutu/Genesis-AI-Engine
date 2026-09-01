import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function run(mode: string) {
  const root = path.resolve(process.cwd(), "..", "..");
  return new Promise<{ ok: boolean; out: string; err: string }>((resolve) => {
    const child = spawn("py", ["-3.12", "-m", "virtus_core.counter_liquidity", mode], {
      cwd: root,
      env: { ...process.env, PYTHONUTF8: "1" },
      windowsHide: true,
    });
    let out = "";
    let err = "";
    const t = setTimeout(() => {
      child.kill();
      resolve({ ok: false, out, err: err + " timeout" });
    }, 60_000);
    child.stdout.on("data", (d) => {
      out += d.toString();
    });
    child.stderr.on("data", (d) => {
      err += d.toString();
    });
    child.on("close", (c) => {
      clearTimeout(t);
      resolve({ ok: c === 0, out, err });
    });
  });
}

function parse(out: string) {
  const start = out.indexOf("{");
  const end = out.lastIndexOf("}");
  return JSON.parse(start >= 0 && end > start ? out.slice(start, end + 1) : out);
}

export async function GET() {
  const result = await run("discover");
  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.err || "liquidity discover failed" }, { status: 500 });
  }
  try {
    return NextResponse.json({ ok: true, ...parse(result.out) });
  } catch {
    return NextResponse.json({ ok: false, error: "parse failed", out: result.out.slice(0, 1500) }, { status: 500 });
  }
}
