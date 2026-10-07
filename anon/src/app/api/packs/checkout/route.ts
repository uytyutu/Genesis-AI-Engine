import crypto from "crypto";
import { z } from "zod";
import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { getProduct, isPackSku } from "@/lib/pricing";
import { createCheckoutSession, markOrderPaid } from "@/lib/stripe";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";
import { secureGiftToken } from "@/lib/anon-id";

const schema = z.object({
  sku: z.string(),
});

/** One-click pack purchase via existing Stripe / sandbox path. */
export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Log in to unlock packs.", 401);

  const rl = await checkRateLimit(`pack_buy:${user.id}`, 20, 60 * 60 * 1000);
  if (!rl.ok) return err("Slow down.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success || !isPackSku(parsed.data.sku)) {
    return err("Unknown pack", 400);
  }

  const product = getProduct(parsed.data.sku);
  if (!product || product.pillar !== "pack") return err("Unknown pack", 400);

  const db = await getDb();
  const giftId = crypto.randomUUID();
  const orderId = crypto.randomUUID();
  const token = secureGiftToken();
  const now = new Date().toISOString();

  await db.prepare(
    `INSERT INTO gifts (
      id, token, sender_id, recipient_id, recipient_label, type, status,
      price_cents, currency, message, media_json, theme, music,
      anonymous, anonymous_id, reveal_enabled, reveal_status,
      open_when_label, unlock_at, opened_at, expires_at, created_at, easter_clicks
    ) VALUES (?, ?, ?, ?, ?, ?, 'awaiting_payment', ?, 'eur', ?, '{}', 'dream', NULL,
      0, NULL, 0, 'hidden', NULL, NULL, NULL, NULL, ?, 0)`
  ).run(
    giftId,
    token,
    user.id,
    user.id,
    user.display_name,
    product.sku,
    product.amountCents,
    `pack:${product.sku}`,
    now
  );

  await db.prepare(
    `INSERT INTO orders (
      id, user_id, gift_id, gift_type, amount_cents, currency,
      stripe_session_id, stripe_payment_id, status, anonymous, reveal_status,
      metadata_json, created_at, paid_at
    ) VALUES (?, ?, ?, ?, ?, 'eur', NULL, NULL, 'pending', 0, 'hidden', ?, ?, NULL)`
  ).run(
    orderId,
    user.id,
    giftId,
    product.sku,
    product.amountCents,
    JSON.stringify({ kind: "pack" }),
    now
  );

  await track("pack_checkout", { sku: product.sku, orderId });

  try {
    const session = await createCheckoutSession({
      orderId,
      giftId,
      amountCents: product.amountCents,
      currency: "eur",
      label: `${product.emoji} ANON · ${product.sku}`,
      successPath: `/plus?unlocked=1&order_id=${orderId}`,
      cancelPath: `/plus?cancelled=1`,
      metadata: { sku: product.sku, kind: "pack" },
    });

    if (session.sandbox) {
      await markOrderPaid({ orderId, stripeSessionId: session.sessionId });
      return json({
        url: `/plus?unlocked=1&order_id=${orderId}&sandbox=1`,
        sandbox: true,
      });
    }

    return json({ url: session.url, sandbox: false });
  } catch (e) {
    return err(e instanceof Error ? e.message : "Checkout failed", 500);
  }
}
