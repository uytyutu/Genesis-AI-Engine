/**
 * M2 client identity token — personal office (separate from guest checkout).
 * localStorage for API Bearer; cookie mirror for Next middleware (server gate).
 */

const TOKEN_KEY = "virtus_client_token";
const NAME_KEY = "virtus_client_name";
const COOKIE_NAME = "virtus_client_token";
const COOKIE_MAX_AGE_SEC = 30 * 24 * 60 * 60;

function writeClientAuthCookie(token: string): void {
  try {
    const secure =
      typeof window !== "undefined" && window.location.protocol === "https:"
        ? "; Secure"
        : "";
    document.cookie = `${COOKIE_NAME}=${encodeURIComponent(token)}; Path=/; Max-Age=${COOKIE_MAX_AGE_SEC}; SameSite=Lax${secure}`;
  } catch {
    /* ignore */
  }
}

function clearClientAuthCookie(): void {
  try {
    document.cookie = `${COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
  } catch {
    /* ignore */
  }
}

export function getClientToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setClientSession(token: string, name?: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    if (name) localStorage.setItem(NAME_KEY, name);
    writeClientAuthCookie(token);
  } catch {
    /* ignore */
  }
}

export function clearClientSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(NAME_KEY);
    clearClientAuthCookie();
  } catch {
    /* ignore */
  }
}

export function clientAuthHeaders(): HeadersInit {
  const token = getClientToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** After M2 auth, also open portal workspace cookie (existing /client shell). */
export async function bridgePortalSession(email: string, password: string): Promise<void> {
  const body = JSON.stringify({
    email: email.trim(),
    password,
    display_name: email.trim().split("@")[0] || "Client",
  });
  try {
    const reg = await fetch("/portal/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body,
    });
    if (reg.ok) {
      const data = (await reg.json()) as { authenticated?: boolean };
      if (data.authenticated) return;
    }
  } catch {
    /* fall through to login */
  }
  try {
    await fetch("/portal/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email: email.trim(), password }),
    });
  } catch {
    /* office shell may still work with M2 token later */
  }
}
