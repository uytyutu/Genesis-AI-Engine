import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { getStripe, markOrderPaid, webhookSecret } from "@/lib/stripe";
import { track } from "@/lib/analytics";
import type Stripe from "stripe";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const stripe = getStripe();
  const secret = webhookSecret();
  if (!stripe || !secret) {
    return err("Webhook not configured", 503);
  }

  const raw = await req.text();
  const sig = req.headers.get("stripe-signature");
  if (!sig) return err("Missing signature", 400);

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(raw, sig, secret);
  } catch {
    return err("Invalid signature", 400);
  }

  const db = await getDb();
  const seen = (await db
    .prepare("SELECT event_id FROM processed_webhooks WHERE event_id = ?")
    .get(event.id));
  if (seen) return json({ received: true, duplicate: true });

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const product = session.metadata?.product;
    if (product && product !== "anon") {
      // Not our product — acknowledge without mutating ANON state
      await db.prepare(
        "INSERT INTO processed_webhooks (event_id, processed_at) VALUES (?, ?)"
      ).run(event.id, new Date().toISOString());
      return json({ received: true, ignored: true });
    }

    const orderId = session.metadata?.order_id;
    if (!orderId) return err("Missing order_id metadata", 400);

    const paymentId =
      typeof session.payment_intent === "string"
        ? session.payment_intent
        : session.payment_intent?.id || null;

    await markOrderPaid({
      orderId,
      stripeSessionId: session.id,
      stripePaymentId: paymentId,
    });
    await track("payment_success", { orderId, via: "webhook" });
  }

  await db.prepare(
    "INSERT INTO processed_webhooks (event_id, processed_at) VALUES (?, ?)"
  ).run(event.id, new Date().toISOString());

  return json({ received: true });
}
