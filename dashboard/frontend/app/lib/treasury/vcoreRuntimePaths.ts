import fs from "fs";
import path from "path";

export function runtimeCandidates(filename: string): string[] {
  const cwd = process.cwd();
  return [
    path.join(cwd, ".runtime", filename),
    path.join(cwd, "..", "..", ".runtime", filename),
    path.join(cwd, "..", ".runtime", filename),
  ];
}

export function readRuntimeJson<T>(filename: string): T | null {
  for (const p of runtimeCandidates(filename)) {
    try {
      if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, "utf8")) as T;
    } catch {
      /* next */
    }
  }
  return null;
}

export function writeRuntimeJson(filename: string, data: unknown): string | null {
  for (const dir of [
    path.join(process.cwd(), ".runtime"),
    path.join(process.cwd(), "..", "..", ".runtime"),
  ]) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      const p = path.join(dir, filename);
      fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf8");
      return p;
    } catch {
      /* try next */
    }
  }
  return null;
}

export function readGenesisState(): Record<string, unknown> | null {
  return readRuntimeJson<Record<string, unknown>>("vcore_genesis_state.json");
}
