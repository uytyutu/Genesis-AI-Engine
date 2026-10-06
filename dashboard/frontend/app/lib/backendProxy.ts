/**
 * Runtime backend proxy target (Oracle-style: env at request time, not baked rewrite).
 * Prefer INTERNAL_API_URL so production can point at a live API without rebuild thrash.
 */
export function backendApiBase(): string {
  const raw = (
    process.env.INTERNAL_API_URL ||
    process.env.GENESIS_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    ""
  ).trim();
  if (!raw) return "";
  return raw.replace(/\/$/, "");
}

export function backendConfigured(): boolean {
  const b = backendApiBase();
  if (!b) return false;
  // Never silently proxy Vercel → localhost (always fails in cloud).
  if (/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(b)) return false;
  return true;
}
