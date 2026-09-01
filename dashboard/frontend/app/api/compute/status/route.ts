import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function repoRoot(): string {
  // dashboard/frontend → repo root
  return path.resolve(process.cwd(), "..", "..");
}

function runPython(args: string[]): Promise<{ ok: boolean; stdout: string; stderr: string; code: number | null }> {
  return new Promise((resolve) => {
    const root = repoRoot();
    const child = spawn("py", ["-3.12", "-m", "virtus_core.compute_engine", ...args], {
      cwd: root,
      env: { ...process.env, PYTHONUTF8: "1" },
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      resolve({ ok: false, stdout, stderr: stderr + "\n[timeout]", code: null });
    }, 90_000);
    child.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    child.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ ok: code === 0, stdout, stderr, code });
    });
  });
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const measure = url.searchParams.get("measure") === "1";
  const args = ["--json"];
  if (measure) args.unshift("--measure");

  const result = await runPython(args);
  if (!result.ok) {
    return NextResponse.json(
      {
        ok: false,
        error: "Compute engine failed",
        stderr: result.stderr.slice(0, 2000),
        stdout: result.stdout.slice(0, 500),
        hint: "Run from repo: npm run compute:audit",
      },
      { status: 500 },
    );
  }
  try {
    // last JSON object in stdout
    const start = result.stdout.indexOf("{");
    const raw = start >= 0 ? result.stdout.slice(start) : result.stdout;
    const data = JSON.parse(raw);
    return NextResponse.json({ ok: true, ...data });
  } catch {
    return NextResponse.json(
      { ok: false, error: "Invalid JSON from engine", stdout: result.stdout.slice(0, 2000) },
      { status: 500 },
    );
  }
}
