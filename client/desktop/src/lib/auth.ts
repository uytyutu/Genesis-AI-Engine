import type { AppSettings } from "./settings";

/** Stage 1 — local credential scaffold only; no server auth yet. */
export type AuthState = {
  configured: boolean;
  maskedKey: string | null;
};

export function getAuthState(settings: AppSettings): AuthState {
  const key = settings.apiKey.trim();
  if (!key) {
    return { configured: false, maskedKey: null };
  }
  const tail = key.slice(-4);
  return { configured: true, maskedKey: `••••${tail}` };
}

export function authHeaders(settings: AppSettings): HeadersInit {
  const key = settings.apiKey.trim();
  if (!key) return {};
  return { Authorization: `Bearer ${key}` };
}
