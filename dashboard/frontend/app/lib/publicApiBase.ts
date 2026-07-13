/** Same-origin /api/* rewrites (next.config) — beta/prod without CORS or baked localhost. */
export function publicApiBase(): string {
  if (typeof window !== "undefined") return "";
  return (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

/** Keep users on the host they opened (beta vs preview vs prod). */
export function normalizePublicHref(href: string | null | undefined): string | null {
  if (!href?.trim()) return null;
  const trimmed = href.trim();
  if (trimmed.startsWith("/")) return trimmed;
  if (typeof window === "undefined") return trimmed;
  try {
    const u = new URL(trimmed);
    const stayOnCurrentHost =
      u.hostname === "genesis-ai-engine.vercel.app" ||
      u.hostname.endsWith(".vercel.app") ||
      u.hostname === "genesis-ai-engine.com" ||
      u.hostname.endsWith(".genesis-ai-engine.com");
    if (stayOnCurrentHost) {
      return `${u.pathname}${u.search}${u.hash}` || "/site";
    }
  } catch {
    /* keep as-is */
  }
  return trimmed;
}

export function rewritePublicSiteUrls(text: string): string {
  if (typeof window === "undefined" || !text) return text;
  const origin = window.location.origin;
  return text.replace(/https?:\/\/genesis-ai-engine\.vercel\.app/gi, origin);
}
