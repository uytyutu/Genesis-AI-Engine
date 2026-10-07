import crypto from "crypto";
import { getSessionUser } from "@/lib/auth";
import { err, json } from "@/lib/api";
import { getSpaceByCode } from "@/lib/viral/store";
import { createCheckoutSession } from "@/lib/stripe";
import { getDb } from "@/lib/db";
import { getProduct } from "@/lib/pricing";

/** Unlock perception map / words mirror for the owner. */
export async function POST(
  _req: Request,
  ctx: { params: Promise<{ code: string }> }
) {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const { code } = await ctx.params;
  const space = await getSpaceByCode(code);
  if (!space) return err("Not found", 404);
  if (space.owner_id !== user.id) return err("Forbidden", 403);
  if (space.unlocked) return json({ ok: true, already: true });

  const sku =
    space.kind === "think"
      ? "VIRAL_THINK_MAP"
      : space.kind === "words"
        ? "VIRAL_WORDS_UNLOCK"
        : null;
  if (!sku) return err("Nothing to unlock", 400);
  const product = getProduct(sku);
  if (!product) return err("Product missing", 500);

  const db = await getDb();
  const orderId = crypto.randomUUID();
  const giftId = crypto.randomUUID();
  const token = crypto.randomBytes(12).toString("hex");
  const now = new Date().toISOString();

  await db
    .prepare(
      `INSERT INTO gifts (
        id, token, sender_id, recipient_id, recipient_label, type, status,
        price_cents, currency, message, media_json, theme, music,
        anonymous, anonymous_id, reveal_enabled, reveal_status,
        open_when_label, unlock_at, opened_at, expires_at, created_at, easter_clicks
      ) VALUES (?, ?, ?, NULL, NULL, ?, 'awaiting_payment', ?, 'eur', ?, ?, 'dream', NULL,
        0, NULL, 1, 'hidden', NULL, NULL, NULL, NULL, ?, 0)`
    )
    .run(
      giftId,
      token,
      user.id,
      sku,
      product.amountCents,
      `Unlock ${space.title}`,
      JSON.stringify({ viralUnlock: { spaceId: space.id, code: space.code, kind: space.kind } }),
      now
    );

  await db
    .prepare(
      `INSERT INTO orders (
        id, user_id, gift_id, gift_type, amount_cents, currency, status,
        anonymous, reveal_status, metadata_json, created_at
      ) VALUES (?, ?, ?, ?, ?, 'eur', 'pending', 0, 'hidden', ?, ?)`
    )
    .run(
      orderId,
      user.id,
      giftId,
      sku,
      product.amountCents,
      JSON.stringify({ viralUnlockCode: space.code, viralSpaceId: space.id }),
      now
    );

  const session = await createCheckoutSession({
    orderId,
    giftId,
    amountCents: product.amountCents,
    currency: "eur",
    label: product.sku,
    successPath: `/orders/success?order_id=${orderId}&viral=1`,
    cancelPath: `/v/${space.code}`,
  });

  return json({
    checkoutUrl: session.url,
    sessionId: session.sessionId,
    sandbox: session.sandbox,
    orderId,
  });
}
