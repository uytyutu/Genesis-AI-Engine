import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function runPython(args: string[]) {
  const root = path.resolve(process.cwd(), "..", "..");
  return new Promise<{ ok: boolean; out: string; err: string }>((resolve) => {
    const child = spawn("py", ["-3.12", "-m", "virtus_core.value_hunter", ...args], {
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

function parseJson(out: string) {
  const start = out.indexOf("{");
  const end = out.lastIndexOf("}");
  const raw = start >= 0 && end > start ? out.slice(start, end + 1) : out;
  return JSON.parse(raw);
}

/** ZERO-CAPITAL SOURCE HUNTER v2.1 pipeline */
export async function GET() {
  const result = await runPython(["--sources"]);
  if (!result.ok) {
    return NextResponse.json(
      { ok: false, error: result.err || "source hunter failed", stdout: result.out.slice(0, 500) },
      { status: 500 },
    );
  }
  try {
    const data = parseJson(result.out);
    return NextResponse.json({ ok: true, ...data });
  } catch {
    return NextResponse.json({ ok: false, error: "parse failed", out: result.out.slice(0, 1500) }, { status: 500 });
  }
}
