import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** Protocol State Discovery — autopsy frictionless bricks (research-only) */
export async function GET(req: Request) {
  const offline = new URL(req.url).searchParams.get("offline") === "1";
  const root = path.resolve(process.cwd(), "..", "..");
  const args = ["-3.12", "-m", "virtus_core.protocol_state_discovery"];
  if (offline) args.push("--offline");

  const result = await new Promise<{ ok: boolean; out: string; err: string }>((resolve) => {
    const child = spawn("py", args, {
      cwd: root,
      env: { ...process.env, PYTHONUTF8: "1" },
      windowsHide: true,
    });
    let out = "";
    let err = "";
    const t = setTimeout(() => {
      child.kill();
      resolve({ ok: false, out, err: err + " timeout" });
    }, 180_000);
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
    return NextResponse.json(
      { ok: false, error: result.err || "protocol discovery failed", stdout: result.out.slice(0, 800) },
      { status: 500 },
    );
  }
  try {
    const start = result.out.indexOf("{");
    const end = result.out.lastIndexOf("}");
    const raw = start >= 0 && end > start ? result.out.slice(start, end + 1) : result.out;
    return NextResponse.json({ ok: true, ...JSON.parse(raw) });
  } catch {
    return NextResponse.json({ ok: false, error: "parse failed", out: result.out.slice(0, 1500) }, { status: 500 });
  }
}
