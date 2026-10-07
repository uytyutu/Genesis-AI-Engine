import { z } from "zod";
import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { createCheckoutSession, markOrderPaid } from "@/lib/stripe";
import { isEngageSku } from "@/lib/engage";
import { getProduct } from "@/lib/pricing";
import { track } from "@/lib/analytics";
import type { GiftRow, OrderRow } from "@/lib/types";

const schema = z.object({
  orderId: z.string().uuid(),
});

export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid order", 400);

  const db = await getDb();
  const order = (await db
    .prepare("SELECT * FROM orders WHERE id = ?")
    .get(parsed.data.orderId)) as OrderRow | undefined;
  if (!order || order.user_id !== user.id) return err("Order not found", 404);
  if (order.status === "paid") {
    const gift = order.gift_id
      ? ((await db.prepare("SELECT token FROM gifts WHERE id = ?").get(order.gift_id)) as
          | { token: string }
          | undefined)
      : null;
    return json({
      alreadyPaid: true,
      sharePath: gift ? `/open/${gift.token}` : "/dashboard",
    });
  }

  const gift = order.gift_id
    ? ((await db.prepare("SELECT * FROM gifts WHERE id = ?").get(order.gift_id)) as unknown as GiftRow | undefined)
    : null;
  if (!gift) return err("Gift missing", 404);

  const product = getProduct(order.gift_type);
  const label = product ? `${product.emoji} ANON · ${order.gift_type}` : `ANON · ${order.gift_type}`;
  const engage = isEngageSku(order.gift_type);
  const successPath = engage
    ? `/orders/success?order_id=${order.id}&engage=1`
    : `/orders/success?order_id=${order.id}`;
  const cancelPath = engage
    ? `/open/${gift.token}?cancelled=1`
    : `/create?cancelled=1&order_id=${order.id}`;

  await track("checkout_started", { orderId: order.id, type: order.gift_type });

  try {
    const session = await createCheckoutSession({
      orderId: order.id,
      giftId: gift.id,
      amountCents: order.amount_cents,
      currency: order.currency,
      label,
      successPath,
      cancelPath,
      metadata: { sku: order.gift_type },
    });

    if (session.sandbox) {
      await markOrderPaid({ orderId: order.id, stripeSessionId: session.sessionId });
      await track("payment_success", { orderId: order.id, sandbox: true });
      return json({
        url: `${successPath}&sandbox=1`,
        sandbox: true,
        sharePath: `/open/${gift.token}`,
        engage,
      });
    }

    return json({ url: session.url, sandbox: false });
  } catch (e) {
    return err(e instanceof Error ? e.message : "Checkout failed", 500);
  }
}
