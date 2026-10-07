import { requireStaff } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { getLaunchBlockers, launchReady } from "@/lib/production-guard";
import { PRODUCTS } from "@/lib/pricing";

export async function GET() {
  const staff = await requireStaff();
  if (!staff) return err("Forbidden", 403);

  let database: "operational" | "down" = "operational";
  try {
    await (await getDb()).prepare("SELECT 1").get();
  } catch {
    database = "down";
  }

  const stripeKey = !!(
    process.env.STRIPE_SECRET_KEY?.trim() || process.env.STRIPE_SECRET_KEY_LIVE?.trim()
  );
  const authSecret = !!process.env.ANON_AUTH_SECRET?.trim();
  const adminEmail = !!process.env.ANON_ADMIN_EMAIL?.trim();

  const checks = {
    api: "operational" as const,
    database,
    auth: authSecret ? ("operational" as const) : ("degraded" as const),
    stripe: stripeKey ? ("operational" as const) : ("degraded" as const),
    telegram: "down" as const,
    voice: "down" as const,
    wallet: "down" as const,
    productsCatalog: Object.keys(PRODUCTS).length > 0 ? ("operational" as const) : ("down" as const),
    adminEmailConfigured: adminEmail,
  };

  // Core path = API + DB + auth. Optional connectors (Telegram/Voice/Wallet) can be Down
  // without marking the whole platform Down.
  const coreDown = checks.database === "down" || checks.api !== "operational";
  const overall = coreDown
    ? "down"
    : checks.auth === "degraded" || checks.stripe === "degraded"
      ? "degraded"
      : "operational";

  return json({
    overall,
    checks,
    launchReady: launchReady(),
    launchBlockers: getLaunchBlockers(),
    note: "Telegram / Voice / Wallet not live — shown as Down, not faked.",
  });
}
