import { json } from "@/lib/api";
import {
  domainReady,
  getLaunchBlockers,
  launchReady,
  publicBaseUrl,
} from "@/lib/production-guard";
import { isSandboxPayments, isStripeReady } from "@/lib/stripe";

/** Public readiness probe — no secrets. */
export async function GET() {
  const localBlockers = getLaunchBlockers();
  const domainBlockers = getLaunchBlockers({ assumeDomain: true });
  return json({
    ok: true,
    service: "anon",
    /** Local/dev may be fine with sandbox */
    launchReady: launchReady(),
    /** Must be true before pointing a public domain here */
    domainReady: domainReady(),
    publicUrlConfigured: Boolean(publicBaseUrl()),
    stripeReady: isStripeReady(),
    sandboxPayments: isSandboxPayments(),
    blockers: localBlockers.map((b) => ({
      id: b.id,
      severity: b.severity,
      message: b.message,
    })),
    domainBlockers: domainBlockers.map((b) => ({
      id: b.id,
      severity: b.severity,
      message: b.message,
    })),
  });
}
