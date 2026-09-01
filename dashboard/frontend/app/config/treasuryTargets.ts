/**
 * Default OWN treasury / ops addresses for liquidity audit.
 * Prefer NEXT_PUBLIC_AUDIT_TARGETS (comma or newline separated) in .env.local.
 * Never put third-party sweep targets here — only wallets you control.
 */
export const DEFAULT_TREASURY_AUDIT_TARGETS: string[] = [
  // Examples — replace with your company hot/cold addresses:
  // "0xYourHotWallet…",
  // "0xYourColdVault…",
];

export const DEFAULT_BTC_AUDIT_TARGETS: string[] = [
  // "bc1q… your company BTC address",
];

/** Poll interval for live liquidity audit (ms). Default off in UI — too aggressive freezes tab. */
export const TREASURY_POLL_MS = 90_000;

export function parseAddressList(raw: string | undefined | null): string[] {
  if (!raw) return [];
  return raw
    .split(/[\n,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/**
 * Resolve ETH audit targets: env overrides file defaults.
 * NEXT_PUBLIC_AUDIT_TARGETS=0xabc...,0xdef...
 */
export function resolveEthAuditTargets(extra: string[] = []): string[] {
  const fromEnv = parseAddressList(
    typeof process !== "undefined" ? process.env.NEXT_PUBLIC_AUDIT_TARGETS : undefined,
  );
  const base = fromEnv.length > 0 ? fromEnv : DEFAULT_TREASURY_AUDIT_TARGETS;
  const seen = new Set<string>();
  const out: string[] = [];
  for (const a of [...base, ...extra]) {
    const k = a.toLowerCase();
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(a);
  }
  return out;
}

export function resolveBtcAuditTargets(extra: string[] = []): string[] {
  const fromEnv = parseAddressList(
    typeof process !== "undefined" ? process.env.NEXT_PUBLIC_BTC_AUDIT_TARGETS : undefined,
  );
  const base = fromEnv.length > 0 ? fromEnv : DEFAULT_BTC_AUDIT_TARGETS;
  const seen = new Set<string>();
  const out: string[] = [];
  for (const a of [...base, ...extra]) {
    const k = a.toLowerCase();
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(a);
  }
  return out;
}
