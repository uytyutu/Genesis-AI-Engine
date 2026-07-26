/**
 * M2 client identity token — personal office (separate from guest checkout).
 */

const TOKEN_KEY = "virtus_client_token";
const NAME_KEY = "virtus_client_name";

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
  } catch {
    /* ignore */
  }
}

export function clearClientSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(NAME_KEY);
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
