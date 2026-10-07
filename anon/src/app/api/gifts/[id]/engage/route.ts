import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import {
  getEngage,
  notifyUser,
  parseMedia,
  setEngage,
} from "@/lib/engage";
import { getProduct } from "@/lib/pricing";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";
import type { GiftRow } from "@/lib/types";

const schema = z.object({
  action: z.enum([
    "ask_hint",
    "ask_reveal",
    "send_hint",
    "decline_hint",
    "decline_reveal",
    "consent_reveal",
    "status",
  ]),
  message: z.string().max(200).optional(),
});

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  const gift = (await (await getDb()).prepare("SELECT * FROM gifts WHERE id = ?").get(id)) as
    | GiftRow
    | undefined;
  if (!gift) return err("Not found", 404);
  if (gift.sender_id !== user.id && gift.recipient_id !== user.id) {
    return err("Forbidden", 403);
  }

  const media = parseMedia(gift.media_json);
  const engage = getEngage(media);
  const isSender = gift.sender_id === user.id;

  return json({
    giftId: gift.id,
    token: gift.token,
    anonymous: Boolean(gift.anonymous),
    role: isSender ? "sender" : "recipient",
    engage: {
      hintRequest: engage.hintRequest?.status || "none",
      revealRequest: engage.revealRequest?.status || "none",
      // Sender hint visible to recipient only after answered
      senderHint:
        engage.hintRequest?.status === "answered" || isSender
          ? engage.senderHint || null
          : null,
    },
  });
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Log in to continue.", 401);

  const rl = await checkRateLimit(`engage:${user.id}`, 40, 60 * 60 * 1000);
  if (!rl.ok) return err("Slow down.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid action", 400);

  const db = await getDb();
  const gift = await db.prepare("SELECT * FROM gifts WHERE id = ?").get(id) as
    | GiftRow
    | undefined;
  if (!gift) return err("Not found", 404);

  const isSender = gift.sender_id === user.id;
  const isRecipient = gift.recipient_id === user.id;
  if (!isSender && !isRecipient) return err("Forbidden", 403);

  const media = parseMedia(gift.media_json);
  const engage = getEngage(media);
  const action = parsed.data.action;

  if (action === "status") {
    return json({
      engage: {
        hintRequest: engage.hintRequest?.status || "none",
        revealRequest: engage.revealRequest?.status || "none",
        senderHint:
          engage.hintRequest?.status === "answered" || isSender
            ? engage.senderHint || null
            : null,
      },
    });
  }

  // —— Recipient paid boosts (create order) ——
  if (action === "ask_hint" || action === "ask_reveal") {
    if (!isRecipient) {
      // Claim open link if nobody claimed yet (not the sender)
      if (!gift.recipient_id && gift.sender_id !== user.id) {
        await db.prepare("UPDATE gifts SET recipient_id = ? WHERE id = ?").run(user.id, gift.id);
      } else {
        return err("Only the recipient can request this.", 403);
      }
    }
    if (!gift.anonymous) return err("This message is not anonymous.", 400);

    const sku = action === "ask_hint" ? "ASK_HINT" : "ASK_REVEAL";
    const product = getProduct(sku)!;
    const existing =
      action === "ask_hint" ? engage.hintRequest?.status : engage.revealRequest?.status;
    if (existing === "pending" || existing === "answered" || existing === "accepted") {
      return err("Already requested.", 409);
    }

    const orderId = crypto.randomUUID();
    const now = new Date().toISOString();
    await db.prepare(
      `INSERT INTO orders (
        id, user_id, gift_id, gift_type, amount_cents, currency,
        stripe_session_id, stripe_payment_id, status, anonymous, reveal_status,
        metadata_json, created_at, paid_at
      ) VALUES (?, ?, ?, ?, ?, 'eur', NULL, NULL, 'pending', 1, 'hidden', ?, ?, NULL)`
    ).run(
      orderId,
      user.id,
      gift.id,
      product.sku,
      product.amountCents,
      JSON.stringify({ engage: true, action, parentGiftId: gift.id }),
      now
    );

    await track("engage_checkout_created", { giftId: gift.id, sku });
    return json(
      {
        orderId,
        sku: product.sku,
        amountCents: product.amountCents,
        free: false,
        next: "checkout",
      },
      201
    );
  }

  // —— Sender responses (free) ——
  if (!isSender) return err("Only the sender can do this.", 403);

  if (action === "send_hint") {
    if (engage.hintRequest?.status !== "pending") {
      return err("No pending hint request.", 400);
    }
    const hint = sanitizeText(parsed.data.message || "", 200);
    if (!hint) return err("Write a short voluntary clue.", 400);

    engage.hintRequest = { ...engage.hintRequest, status: "answered" };
    engage.senderHint = hint;
    await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
      setEngage(media, engage),
      gift.id
    );

    if (gift.recipient_id) {
      await notifyUser({
        userId: gift.recipient_id,
        type: "hint_received",
        title: "A clue arrived",
        body: "Open the message — still anonymous.",
        href: `/open/${gift.token}`,
      });
    }
    await track("engage_hint_sent", { giftId: gift.id });
    return json({ ok: true, engage: { hintRequest: "answered" } });
  }

  if (action === "decline_hint") {
    if (engage.hintRequest?.status !== "pending") {
      return err("No pending hint request.", 400);
    }
    engage.hintRequest = { ...engage.hintRequest, status: "declined" };
    await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
      setEngage(media, engage),
      gift.id
    );
    if (gift.recipient_id) {
      await notifyUser({
        userId: gift.recipient_id,
        type: "hint_declined",
        title: "They stayed fully anonymous",
        body: "No clue this time — you can still reply.",
        href: `/open/${gift.token}`,
      });
    }
    return json({ ok: true, engage: { hintRequest: "declined" } });
  }

  if (action === "decline_reveal") {
    if (engage.revealRequest?.status !== "pending") {
      return err("No pending reveal request.", 400);
    }
    engage.revealRequest = { ...engage.revealRequest, status: "declined" };
    await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
      setEngage(media, engage),
      gift.id
    );
    if (gift.recipient_id) {
      await notifyUser({
        userId: gift.recipient_id,
        type: "reveal_declined",
        title: "They chose to stay ANON",
        body: "Identity stays hidden. You can keep chatting.",
        href: `/open/${gift.token}`,
      });
    }
    return json({ ok: true, engage: { revealRequest: "declined" } });
  }

  if (action === "consent_reveal") {
    // Mark sender accepted the request; still need mutual cinematic via /api/anonymous reveal
    media.revealConsentSender = true;
    if (engage.revealRequest) {
      engage.revealRequest = { ...engage.revealRequest, status: "accepted" };
    }
    await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
      setEngage(media, engage),
      gift.id
    );
    if (gift.recipient_id) {
      await notifyUser({
        userId: gift.recipient_id,
        type: "reveal_accepted",
        title: "They may be ready to open up",
        body: "Mutual reveal still needs both sides — open the message.",
        href: `/open/${gift.token}`,
      });
    }
    return json({ ok: true, engage: { revealRequest: "accepted" }, consentSender: true });
  }

  return err("Unknown action", 400);
}
