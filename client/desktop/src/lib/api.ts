import type { AppSettings } from "./settings";
import { authHeaders } from "./auth";

export type SystemStatus = {
  name: string;
  version: string;
  phase: string;
  paused: boolean;
  uptime_sec: number | null;
};

export type ApiPingResult =
  | { ok: true; status: SystemStatus; latencyMs: number }
  | { ok: false; error: string };

function apiBase(settings: AppSettings): string {
  return settings.apiUrl.replace(/\/$/, "");
}

export async function pingApi(settings: AppSettings): Promise<ApiPingResult> {
  const started = performance.now();
  try {
    const res = await fetch(`${apiBase(settings)}/api/status`, {
      headers: {
        Accept: "application/json",
        ...authHeaders(settings),
      },
    });
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}` };
    }
    const status = (await res.json()) as SystemStatus;
    return { ok: true, status, latencyMs: Math.round(performance.now() - started) };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Network error";
    return { ok: false, error: message };
  }
}
