import type { AppSettings } from "./settings";
import { authHeaders } from "./auth";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export function apiBase(settings: AppSettings): string {
  return settings.apiUrl.replace(/\/$/, "");
}

export async function apiJson<T>(
  settings: AppSettings,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${apiBase(settings)}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...authHeaders(settings),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    throw new ApiError(res.status, `HTTP ${res.status}`);
  }

  return (await res.json()) as T;
}
