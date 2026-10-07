/**
 * Production launch guards — fail loud before fake money / localhost URLs ship.
 */

export function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production";
}

export function publicBaseUrl(): string {
  return (process.env.ANON_PUBLIC_URL || "").trim().replace(/\/$/, "");
}

export function isLocalPublicUrl(url: string): boolean {
  if (!url) return true;
  try {
    const u = new URL(url);
    return (
      u.hostname === "localhost" ||
      u.hostname === "127.0.0.1" ||
      u.hostname.endsWith(".local")
    );
  } catch {
    return true;
  }
}

export type LaunchBlocker = {
  id: string;
  severity: "block" | "warn";
  message: string;
};

/** Checks that must be green before pointing a real domain at ANON. */
export function getLaunchBlockers(opts?: { assumeDomain?: boolean }): LaunchBlocker[] {
  const blockers: LaunchBlocker[] = [];
  const base = publicBaseUrl();
  const sandbox = process.env.ANON_PAYMENT_SANDBOX?.trim() === "1";
  const hasStripe = Boolean(
    process.env.STRIPE_SECRET_KEY?.trim() || process.env.STRIPE_SECRET_KEY_LIVE?.trim()
  );
  const authSecret = process.env.ANON_AUTH_SECRET?.trim() || "";
  const prod = isProductionRuntime();
  /** Pretend we are on a public domain (for preflight from localhost). */
  const domainGate = Boolean(opts?.assumeDomain) || (prod && !isLocalPublicUrl(base));

  if (!base) {
    blockers.push({
      id: "public_url_missing",
      severity: "block",
      message: "ANON_PUBLIC_URL is required (Stripe redirects + metadataBase).",
    });
  } else if (domainGate && isLocalPublicUrl(base)) {
    blockers.push({
      id: "public_url_localhost",
      severity: "block",
      message: "ANON_PUBLIC_URL still points at localhost — set https://your.domain before deploy.",
    });
  }

  if (domainGate && sandbox && !hasStripe) {
    blockers.push({
      id: "sandbox_on_public",
      severity: "block",
      message:
        "ANON_PAYMENT_SANDBOX=1 with no Stripe key — real users would get fake checkout.",
    });
  }

  if (domainGate && sandbox && hasStripe) {
    blockers.push({
      id: "sandbox_flag_ignored",
      severity: "warn",
      message:
        "ANON_PAYMENT_SANDBOX=1 but Stripe key present — live Stripe is used (sandbox ignored).",
    });
  }

  if (!authSecret || authSecret === "change-me-to-a-long-random-string" || authSecret.length < 24) {
    blockers.push({
      id: "weak_auth_secret",
      severity: domainGate || prod ? "block" : "warn",
      message: "ANON_AUTH_SECRET must be a long random string before public launch.",
    });
  }

  if (domainGate && !hasStripe) {
    blockers.push({
      id: "stripe_missing",
      severity: "block",
      message: "STRIPE_SECRET_KEY (or _LIVE) required for paid Drop / Moments / Open Later.",
    });
  }

  if (
    domainGate &&
    !process.env.STRIPE_WEBHOOK_SECRET?.trim() &&
    !process.env.ANON_STRIPE_WEBHOOK_SECRET?.trim()
  ) {
    blockers.push({
      id: "webhook_secret_missing",
      severity: "warn",
      message: "Set STRIPE_WEBHOOK_SECRET or ANON_STRIPE_WEBHOOK_SECRET for reliable paid fulfillment.",
    });
  }

  return blockers;
}

/** Runtime-aware (local sandbox OK). */
export function launchReady(): boolean {
  return getLaunchBlockers().every((b) => b.severity !== "block");
}

/** Would this env be safe on a real domain? Use before DNS cutover. */
export function domainReady(): boolean {
  return getLaunchBlockers({ assumeDomain: true }).every((b) => b.severity !== "block");
}
