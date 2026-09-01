import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const root = path.resolve(process.cwd(), "..", "..");
  const code = `
import json, sys
sys.path.insert(0, r${JSON.stringify(root)})
from virtus_core.compute_engine.hardware import detect_hardware
print(json.dumps(detect_hardware().to_dict(), ensure_ascii=False))
`;
  const result = await new Promise<{ ok: boolean; out: string; err: string }>((resolve) => {
    const child = spawn("py", ["-3.12", "-c", code], {
      cwd: root,
      env: { ...process.env, PYTHONUTF8: "1" },
      windowsHide: true,
    });
    let out = "";
    let err = "";
    const t = setTimeout(() => {
      child.kill();
      resolve({ ok: false, out, err: err + " timeout" });
    }, 30_000);
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

  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.err || "hardware scan failed" }, { status: 500 });
  }
  try {
    const data = JSON.parse(result.out.trim());
    return NextResponse.json({ ok: true, hardware: data });
  } catch {
    return NextResponse.json({ ok: false, error: "parse failed", out: result.out }, { status: 500 });
  }
}
