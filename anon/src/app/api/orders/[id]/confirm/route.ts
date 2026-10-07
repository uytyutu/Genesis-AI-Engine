import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { isEngageSku } from "@/lib/engage";
import { getStripe, markOrderPaid } from "@/lib/stripe";
import type { GiftRow, OrderRow } from "@/lib/types";

/** Redirect fallback when webhook is slow — still server-side Stripe retrieve. */
export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  const db = await getDb();
  const order = (await db.prepare("SELECT * FROM orders WHERE id = ?").get(id)) as unknown as OrderRow | undefined;
  if (!order || order.user_id !== user.id) return err("Not found", 404);

  if (order.status === "paid") {
    return json(await paidPayload(db, order));
  }

  let body: { sessionId?: string; sandbox?: boolean } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }

  if (body.sandbox && order.stripe_session_id?.startsWith("sandbox_")) {
    await markOrderPaid({ orderId: order.id, stripeSessionId: order.stripe_session_id });
  } else if (body.sessionId) {
    const stripe = getStripe();
    if (!stripe) return err("Stripe not configured", 503);
    const session = await stripe.checkout.sessions.retrieve(body.sessionId);
    if (session.payment_status !== "paid") return err("Payment not confirmed", 402);
    if (session.metadata?.order_id !== order.id) return err("Session mismatch", 400);
    const paymentId =
      typeof session.payment_intent === "string"
        ? session.payment_intent
        : session.payment_intent?.id || null;
    await markOrderPaid({
      orderId: order.id,
      stripeSessionId: session.id,
      stripePaymentId: paymentId,
    });
  } else {
    return err("Nothing to confirm", 400);
  }

  const refreshed = (await db.prepare("SELECT * FROM orders WHERE id = ?").get(id)) as unknown as OrderRow;
  return json(await paidPayload(db, refreshed));
}

async function paidPayload(db: Awaited<ReturnType<typeof getDb>>, order: OrderRow) {
  const gift = order.gift_id
    ? ((await db.prepare("SELECT * FROM gifts WHERE id = ?").get(order.gift_id)) as GiftRow | undefined)
    : null;

  let sharePath: string | null = gift ? `/open/${gift.token}` : null;
  if (order.gift_type?.startsWith("VIRAL_") && gift?.media_json) {
    try {
      const media = JSON.parse(gift.media_json) as {
        viral?: { sharePath?: string; code?: string };
        viralUnlock?: { code?: string };
      };
      if (media.viral?.sharePath) sharePath = media.viral.sharePath;
      else if (media.viral?.code) sharePath = `/s/${media.viral.code}`;
      else if (media.viralUnlock?.code) sharePath = `/v/${media.viralUnlock.code}`;
    } catch {
      /* keep default */
    }
  }
  try {
    const meta = JSON.parse(order.metadata_json || "{}") as { sharePath?: string; viralCode?: string };
    if (meta.sharePath) sharePath = meta.sharePath;
    else if (meta.viralCode) sharePath = `/s/${meta.viralCode}`;
  } catch {
    /* ignore */
  }

  return {
    paid: true,
    engage: isEngageSku(order.gift_type),
    viral: Boolean(order.gift_type?.startsWith("VIRAL_")),
    sharePath,
  };
}
