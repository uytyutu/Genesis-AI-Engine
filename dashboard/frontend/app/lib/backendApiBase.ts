/** Shared browser API base — must match Launcher backend (:8000). */

export const LAUNCHER_BACKEND_DEFAULT = "http://localhost:8000";

export function getBackendApiBase(): string {
  const fromEnv = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
  return fromEnv || LAUNCHER_BACKEND_DEFAULT;
}

export type BackendReachability = {
  ok: boolean;
  apiBase: string;
  statusCode: number | null;
  healthCode: number | null;
  reason:
    | "ok"
    | "connection_refused"
    | "timeout"
    | "http_error"
    | "unknown";
  detail: string;
};

/** Probe Launcher health endpoints — used when Farm/API fetch fails. */
export async function probeBackendReachability(
  apiBase: string = getBackendApiBase(),
  timeoutMs = 4_000,
): Promise<BackendReachability> {
  const base = apiBase.replace(/\/$/, "");
  const ctrl = new AbortController();
  const kill = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const [statusRes, healthRes] = await Promise.all([
      fetch(`${base}/api/status`, { signal: ctrl.signal, cache: "no-store" }).catch(
        () => null,
      ),
      fetch(`${base}/health`, { signal: ctrl.signal, cache: "no-store" }).catch(() => null),
    ]);
    clearTimeout(kill);
    const statusCode = statusRes?.status ?? null;
    const healthCode = healthRes?.status ?? null;
    if (statusRes?.ok || healthRes?.ok) {
      return {
        ok: true,
        apiBase: base,
        statusCode,
        healthCode,
        reason: "ok",
        detail: "Backend отвечает",
      };
    }
    if (statusRes || healthRes) {
      return {
        ok: false,
        apiBase: base,
        statusCode,
        healthCode,
        reason: "http_error",
        detail: `Backend на ${base} ответил HTTP ${statusCode ?? healthCode ?? "?"} — не connection refused`,
      };
    }
    return {
      ok: false,
      apiBase: base,
      statusCode: null,
      healthCode: null,
      reason: "connection_refused",
      detail:
        `Нет ответа с ${base} (/api/status, /health). ` +
        "Virtus Core остановлен или Backend упал — запустите Genesis.exe. " +
        "См. launcher/logs/backend.log",
    };
  } catch (e) {
    clearTimeout(kill);
    const aborted = e instanceof DOMException && e.name === "AbortError";
    return {
      ok: false,
      apiBase: base,
      statusCode: null,
      healthCode: null,
      reason: aborted ? "timeout" : "unknown",
      detail: aborted
        ? `Таймаут probe ${base} — Backend не отвечает вовремя`
        : `Probe failed: ${e instanceof Error ? e.message : String(e)}`,
    };
  }
}
