import type { AppSettings } from "./settings";
import { authHeaders } from "./auth";
import { apiJson, apiBase } from "./apiClient";

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

export { apiBase };

export async function pingApi(settings: AppSettings): Promise<ApiPingResult> {
  const started = performance.now();
  try {
    const status = await apiJson<SystemStatus>(settings, "/api/status", {
      headers: { Accept: "application/json", ...authHeaders(settings) },
    });
    return { ok: true, status, latencyMs: Math.round(performance.now() - started) };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Network error";
    return { ok: false, error: message };
  }
}
