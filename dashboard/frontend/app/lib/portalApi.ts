/**
 * Thin Portal HTTP client — credentials only, no domain logic.
 * Paths are same-origin via next.config `/portal` rewrite.
 */

export class PortalApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail || `portal_http_${status}`);
    this.name = "PortalApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail != null) return JSON.stringify(body.detail);
  } catch {
    /* ignore */
  }
  return res.statusText || `http_${res.status}`;
}

export async function portalFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(path.startsWith("/") ? path : `/${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    throw new PortalApiError(res.status, await parseDetail(res));
  }
  if (res.status === 404) {
    throw new PortalApiError(404, await parseDetail(res));
  }
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export async function portalFetchAllow404<T = unknown>(
  path: string,
): Promise<T | null> {
  const res = await fetch(path, { credentials: "include" });
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new PortalApiError(res.status, await parseDetail(res));
  }
  return (await res.json()) as T;
}
