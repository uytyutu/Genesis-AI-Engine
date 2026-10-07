import crypto from "crypto";
import { z } from "zod";
import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { createCheckoutSession, markOrderPaid } from "@/lib/stripe";
import { PRODUCTS } from "@/lib/pricing";
import { track } from "@/lib/analytics";
import type { AnonIdentityRow, GiftRow } from "@/lib/types";

/**
 * Reveal Moment — mutual consent first, then optional paid cinematic reveal.
 * Never sells a name the system cannot show.
 */
export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id: giftId } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  let body: { action?: string } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  const action = body.action || "checkout";

  const db = await getDb();
  const gift = await db.prepare("SELECT * FROM gifts WHERE id = ?").get(giftId) as GiftRow | undefined;
  if (!gift) return err("Not found", 404);
  if (!gift.anonymous || !gift.anonymous_id) return err("This gift is not anonymous.", 400);
  if (!gift.reveal_enabled) return err("Reveal is disabled for this gift.", 400);

  const anon = (await db
    .prepare("SELECT * FROM anon_identities WHERE id = ?")
    .get(gift.anonymous_id)) as AnonIdentityRow | undefined;
  if (!anon) return err("Anonymous identity missing", 400);
  if (anon.owner_user_id !== gift.sender_id) {
    return err("Reveal is not available for this identity.", 400);
  }
  if (anon.is_revealed || gift.reveal_status === "revealed") {
    return json({ alreadyRevealed: true });
  }

  const media = safeMedia(gift.media_json);
  const isSender = gift.sender_id === user.id;
  const isRecipient = gift.recipient_id === user.id;
  if (!isSender && !isRecipient) return err("Only chat participants can consent.", 403);

  if (action === "consent") {
    if (isSender) media.revealConsentSender = true;
    if (isRecipient) media.revealConsentRecipient = true;
    await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
      JSON.stringify(media),
      gift.id
    );
    return json({
      consent: {
        sender: Boolean(media.revealConsentSender),
        recipient: Boolean(media.revealConsentRecipient),
      },
      ready: Boolean(media.revealConsentSender && media.revealConsentRecipient),
    });
  }

  if (action === "status") {
    return json({
      consent: {
        sender: Boolean(media.revealConsentSender),
        recipient: Boolean(media.revealConsentRecipient),
      },
      ready: Boolean(media.revealConsentSender && media.revealConsentRecipient),
      revealStatus: gift.reveal_status,
    });
  }

  // Paid Reveal Moment — only after both consented, and identity is real
  if (!media.revealConsentSender || !media.revealConsentRecipient) {
    return err("Both sides must agree before Reveal Moment.", 400, "consent_required");
  }
  if (!isSender) return err("Sender starts the paid Reveal Moment.", 403);

  const product = PRODUCTS.SEND_REVEAL;
  const orderId = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO orders (
      id, user_id, gift_id, gift_type, amount_cents, currency,
      stripe_session_id, stripe_payment_id, status, anonymous, reveal_status,
      metadata_json, created_at, paid_at
    ) VALUES (?, ?, ?, ?, ?, 'eur', NULL, NULL, 'pending', 1, 'available', ?, ?, NULL)`
  ).run(
    orderId,
    user.id,
    gift.id,
    product.sku,
    product.amountCents,
    JSON.stringify({ purpose: "reveal_moment", anonIdentityId: anon.id }),
    now
  );

  await track("reveal_purchase", { giftId: gift.id, orderId, mutual: true });

  try {
    const session = await createCheckoutSession({
      orderId,
      giftId: gift.id,
      amountCents: product.amountCents,
      currency: "eur",
      label: "🔓 ANON Reveal Moment",
      successPath: `/orders/success?order_id=${orderId}&reveal=1`,
      cancelPath: `/dashboard?reveal_cancelled=1`,
      metadata: { sku: product.sku, purpose: "reveal_moment" },
    });

    if (session.sandbox) {
      await markOrderPaid({ orderId, stripeSessionId: session.sessionId });
      return json({ revealed: true, sandbox: true, revealMoment: true });
    }
    return json({ url: session.url, revealMoment: true });
  } catch (e) {
    return err(e instanceof Error ? e.message : "Checkout failed", 500);
  }
}

function safeMedia(raw: string): Record<string, unknown> {
  try {
    return JSON.parse(raw || "{}") as Record<string, unknown>;
  } catch {
    return {};
  }
}
