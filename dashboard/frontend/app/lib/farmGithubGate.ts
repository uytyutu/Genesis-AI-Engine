/** Farm Engine — GitHub opens only after explicit user action.

Virtus Core Farm uses PAT (GITHUB_TOKEN), never OAuth.
Any window.open / location to github.com without an explicit allow
token is blocked so «Select an account» cannot loop from Farm code.
*/

const ALLOW_KEY = "__farmGithubOpenAllowUntil";

export function isGithubHost(raw: string): boolean {
  try {
    const u = new URL(raw, typeof window !== "undefined" ? window.location.href : "http://local");
    return u.hostname === "github.com" || u.hostname === "www.github.com";
  } catch {
    return /github\.com/i.test(raw);
  }
}

export function isGithubAuthPath(raw: string): boolean {
  if (!isGithubHost(raw)) return false;
  try {
    const u = new URL(raw, typeof window !== "undefined" ? window.location.href : "http://local");
    return (
      u.pathname.startsWith("/login") ||
      u.pathname.startsWith("/sessions") ||
      u.pathname.includes("/login/oauth")
    );
  } catch {
    return false;
  }
}

/** One-shot allow for the next openExternalGithub call (user gesture). */
export function armGithubOpen(ms = 4000): void {
  if (typeof window === "undefined") return;
  (window as unknown as Record<string, number>)[ALLOW_KEY] = Date.now() + ms;
}

export function isGithubOpenArmed(): boolean {
  if (typeof window === "undefined") return false;
  const until = (window as unknown as Record<string, number>)[ALLOW_KEY] || 0;
  return Date.now() < until;
}

export function disarmGithubOpen(): void {
  if (typeof window === "undefined") return;
  delete (window as unknown as Record<string, number>)[ALLOW_KEY];
}

/**
 * Open a GitHub URL only after armGithubOpen() in the same click handler.
 * Auth URLs are never opened from Farm.
 */
export function openExternalGithub(url: string): { ok: boolean; reason?: string } {
  const href = (url || "").trim();
  if (!href) return { ok: false, reason: "empty" };
  if (!isGithubHost(href)) {
    window.open(href, "_blank", "noopener,noreferrer");
    return { ok: true };
  }
  if (isGithubAuthPath(href)) {
    return { ok: false, reason: "github_auth_blocked" };
  }
  if (!isGithubOpenArmed()) {
    return { ok: false, reason: "not_armed" };
  }
  // Keep arm until window.open patch sees it (patch disarms). Fallback disarm after.
  window.open(href, "_blank", "noopener,noreferrer");
  disarmGithubOpen();
  return { ok: true };
}

/** Click handler for UI: arm → open → report. */
export function onGithubLinkClick(url: string, onBlocked?: (reason: string) => void): void {
  armGithubOpen();
  const res = openExternalGithub(url);
  if (!res.ok && onBlocked) onBlocked(res.reason || "blocked");
}
