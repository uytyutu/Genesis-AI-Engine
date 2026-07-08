/** Fetch with timeout — Mission Control must not hang the browser when Backend is slow. */

export type FetchApiInit = RequestInit & { timeoutMs?: number };

export async function fetchApi(input: string, init?: FetchApiInit): Promise<Response> {
  const timeoutMs = init?.timeoutMs ?? 12_000;
  const { timeoutMs: _drop, ...rest } = init ?? {};
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...rest, signal: controller.signal });
  } finally {
    window.clearTimeout(timer);
  }
}
