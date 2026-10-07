import Stripe from "stripe";
import { getDb } from "./db";
import { fulfillEngageOrder } from "./engage";
import { entitlementsForSku, grantEntitlement } from "./entitlements";
import { createViralSpace, markUnlocked } from "./viral/store";
import type { ViralKind } from "./viral/catalog";
import type { OrderRow } from "./types";

/** Resolve secret the same way Virtus does — prefer live alias when primary is test/missing. */
export function resolveStripeSecret(): string {
  const primary = process.env.STRIPE_SECRET_KEY?.trim() || "";
  const liveAlias = process.env.STRIPE_SECRET_KEY_LIVE?.trim() || "";
  if (liveAlias.startsWith("sk_live_") && (!primary || primary.startsWith("sk_test_"))) {
    return liveAlias;
  }
  return primary || liveAlias;
}

export function isSandboxPayments(): boolean {
  if (resolveStripeSecret()) return false;
  if (process.env.ANON_PAYMENT_SANDBOX?.trim() !== "1") return false;
  // Never sandbox-charge on a public production host without a Stripe key.
  const base = (process.env.ANON_PUBLIC_URL || "").trim();
  const isLocal =
    !base ||
    base.includes("localhost") ||
    base.includes("127.0.0.1");
  if (process.env.NODE_ENV === "production" && !isLocal) {
    return false;
  }
  return true;
}

export function isStripeReady(): boolean {
  return Boolean(resolveStripeSecret());
}

export function getStripe(): Stripe | null {
  const key = resolveStripeSecret();
  if (!key) return null;
  return new Stripe(key);
}

export function publicUrl(path = ""): string {
  const fromEnv = (process.env.ANON_PUBLIC_URL || "").trim().replace(/\/$/, "");
  // Local/dev fallback only — production must set ANON_PUBLIC_URL (see production-guard).
  const base = fromEnv || "http://localhost:3100";
  if (!path) return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function createCheckoutSession(input: {
  orderId: string;
  giftId: string;
  amountCents: number;
  currency: string;
  label: string;
  successPath: string;
  cancelPath: string;
  metadata?: Record<string, string>;
}): Promise<{ url: string; sessionId: string | null; sandbox: boolean }> {
  const db = await getDb();

  if (isSandboxPayments()) {
    const sessionId = `sandbox_${input.orderId}`;
    await db.prepare(
      `UPDATE orders SET stripe_session_id = ?, status = 'pending' WHERE id = ?`
    ).run(sessionId, input.orderId);
    return {
      url: publicUrl(
        `${input.successPath}${input.successPath.includes("?") ? "&" : "?"}sandbox=1&order_id=${input.orderId}`
      ),
      sessionId,
      sandbox: true,
    };
  }

  const stripe = getStripe();
  if (!stripe) {
    throw new Error("Stripe is not configured. Set STRIPE_SECRET_KEY or ANON_PAYMENT_SANDBOX=1");
  }

  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    success_url: publicUrl(
      `${input.successPath}${input.successPath.includes("?") ? "&" : "?"}session_id={CHECKOUT_SESSION_ID}`
    ),
    cancel_url: publicUrl(input.cancelPath),
    line_items: [
      {
        quantity: 1,
        price_data: {
          currency: input.currency,
          unit_amount: input.amountCents,
          product_data: {
            name: input.label,
            description: "ANON — send a moment",
          },
        },
      },
    ],
    metadata: {
      product: "anon",
      order_id: input.orderId,
      gift_id: input.giftId,
      ...(input.metadata || {}),
    },
    payment_intent_data: {
      metadata: {
        product: "anon",
        order_id: input.orderId,
        gift_id: input.giftId,
      },
    },
  });

  await db.prepare(
    `UPDATE orders SET stripe_session_id = ? WHERE id = ?`
  ).run(session.id, input.orderId);

  if (!session.url) throw new Error("Stripe did not return a checkout URL");
  return { url: session.url, sessionId: session.id, sandbox: false };
}

/** Server-side unlock — never trust frontend paid=true. */
export async function markOrderPaid(params: {
  orderId: string;
  stripeSessionId?: string | null;
  stripePaymentId?: string | null;
}): Promise<OrderRow | null> {
  const db = await getDb();
  const order = (await db
    .prepare("SELECT * FROM orders WHERE id = ?")
    .get(params.orderId)) as OrderRow | undefined;
  if (!order) return null;

  if (order.status === "paid") {
    return order; // idempotent
  }

  const paidAt = new Date().toISOString();
  await db.prepare(
    `UPDATE orders
     SET status = 'paid',
         paid_at = ?,
         stripe_session_id = COALESCE(?, stripe_session_id),
         stripe_payment_id = COALESCE(?, stripe_payment_id)
     WHERE id = ?`
  ).run(
    paidAt,
    params.stripeSessionId ?? null,
    params.stripePaymentId ?? null,
    params.orderId
  );

  if (order.gift_id) {
    const giftType = order.gift_type;
    if (giftType === "ASK_HINT" || giftType === "ASK_REVEAL") {
      await fulfillEngageOrder({
        id: order.id,
        gift_id: order.gift_id,
        gift_type: giftType,
        user_id: order.user_id,
      });
    } else if (
      giftType.startsWith("VIRAL_") &&
      order.gift_id
    ) {
      await fulfillViralOrder(order);
    } else if (giftType === "SEND_REVEAL") {
      await db.prepare(
        `UPDATE gifts SET reveal_status = 'revealed' WHERE id = ?`
      ).run(order.gift_id);
      const gift = (await db
        .prepare("SELECT anonymous_id, sender_id FROM gifts WHERE id = ?")
        .get(order.gift_id)) as
        | { anonymous_id: string | null; sender_id: string | null }
        | undefined;
      if (gift?.anonymous_id) {
        await db.prepare(
          `UPDATE anon_identities SET is_revealed = 1 WHERE id = ?`
        ).run(gift.anonymous_id);
      }
      await db.prepare(
        `UPDATE orders SET reveal_status = 'revealed' WHERE id = ?`
      ).run(params.orderId);
    } else {
      await db.prepare(
        `UPDATE gifts SET status = 'paid' WHERE id = ? AND status IN ('draft','awaiting_payment')`
      ).run(order.gift_id);
      await db.prepare(
        `UPDATE gifts SET status = 'sent' WHERE id = ? AND status = 'paid'`
      ).run(order.gift_id);
    }
  }

  if (order.user_id) {
    for (const key of entitlementsForSku(order.gift_type)) {
      await grantEntitlement(order.user_id, key, order.gift_type);
    }
  }

  return (await db.prepare("SELECT * FROM orders WHERE id = ?").get(params.orderId)) as unknown as OrderRow;
}

async function fulfillViralOrder(order: OrderRow): Promise<void> {
  const db = await getDb();
  if (!order.gift_id) return;
  const gift = (await db
    .prepare("SELECT * FROM gifts WHERE id = ?")
    .get(order.gift_id)) as { media_json?: string; status?: string } | undefined;
  if (!gift) return;

  let media: Record<string, unknown> = {};
  try {
    media = JSON.parse(gift.media_json || "{}") as Record<string, unknown>;
  } catch {
    media = {};
  }

  const unlock = media.viralUnlock as { spaceId?: string; code?: string } | undefined;
  if (unlock?.spaceId) {
    await markUnlocked(unlock.spaceId);
    await db
      .prepare(`UPDATE gifts SET status = 'paid' WHERE id = ?`)
      .run(order.gift_id);
    return;
  }

  const viral = media.viral as
    | { kind?: string; title?: string; config?: Record<string, unknown> }
    | undefined;
  if (!viral?.kind || !order.user_id) {
    await db
      .prepare(`UPDATE gifts SET status = 'paid' WHERE id = ?`)
      .run(order.gift_id);
    return;
  }

  const space = await createViralSpace({
    kind: viral.kind as ViralKind,
    ownerId: order.user_id,
    title: viral.title || "ANON",
    config: viral.config || {},
  });

  await db
    .prepare(
      `UPDATE gifts SET status = 'sent', media_json = ? WHERE id = ?`
    )
    .run(
      JSON.stringify({
        ...media,
        viral: { ...viral, code: space.code, path: `/v/${space.code}`, sharePath: `/s/${space.code}` },
      }),
      order.gift_id
    );

  await db
    .prepare(`UPDATE orders SET metadata_json = ? WHERE id = ?`)
    .run(
      JSON.stringify({
        ...(typeof order.metadata_json === "string"
          ? JSON.parse(order.metadata_json || "{}")
          : {}),
        viralCode: space.code,
        sharePath: `/s/${space.code}`,
      }),
      order.id
    );
}

export function webhookSecret(): string {
  return (
    process.env.ANON_STRIPE_WEBHOOK_SECRET?.trim() ||
    process.env.STRIPE_WEBHOOK_SECRET?.trim() ||
    ""
  );
}
