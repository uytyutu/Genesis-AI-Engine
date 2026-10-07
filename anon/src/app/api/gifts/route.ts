import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { createAnonIdentity, generateRecipientLabel, secureGiftToken } from "@/lib/anon-id";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { DROP_MOODS, getProduct, THEMES } from "@/lib/pricing";
import { moodToTheme } from "@/lib/themes";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";
import type { GiftRow } from "@/lib/types";

const createSchema = z.object({
  type: z.string(),
  message: z.string().min(1).max(4000),
  recipientLabel: z.string().max(80).optional(),
  theme: z.string().optional(),
  anonymous: z.boolean().optional(),
  openWhenLabel: z.string().max(120).optional(),
  unlockAt: z.string().datetime().optional().nullable(),
  revealEnabled: z.boolean().optional(),
  mood: z.string().optional(),
  media: z.record(z.string(), z.unknown()).optional(),
});

export async function GET() {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const db = await getDb();
  const sent = (await db
    .prepare(
      `SELECT id, token, type, status, price_cents, currency, anonymous, anonymous_id,
              reveal_status, opened_at, created_at, recipient_label, theme, media_json
       FROM gifts WHERE sender_id = ? ORDER BY created_at DESC LIMIT 100`
    )
    .all(user.id));
  const received = (await db
    .prepare(
      `SELECT id, token, type, status, price_cents, currency, anonymous, anonymous_id,
              reveal_status, opened_at, created_at, recipient_label, theme, media_json
       FROM gifts WHERE recipient_id = ? ORDER BY created_at DESC LIMIT 100`
    )
    .all(user.id));
  return json({ sent, received });
}

export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Log in to create a gift.", 401);

  const rl = await checkRateLimit(`gift_create:${user.id}`, 30, 60 * 60 * 1000);
  if (!rl.ok) return err("Easy — too many gifts. Wait a bit.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = createSchema.safeParse(body);
  if (!parsed.success) return err("Invalid gift payload", 400);

  const product = getProduct(parsed.data.type);
  if (
    !product ||
    product.sku === "SEND_REVEAL" ||
    product.pillar === "engage"
  ) {
    return err("Unknown gift type", 400);
  }

  const isAnon = Boolean(parsed.data.anonymous || product.pillar === "anon");
  let anonymousId: string | null = null;
  if (isAnon) {
    anonymousId = (await createAnonIdentity(user.id)).id;
  }

  const id = crypto.randomUUID();
  const token = secureGiftToken();
  const now = new Date().toISOString();

  const mood =
    parsed.data.mood && (DROP_MOODS as readonly string[]).includes(parsed.data.mood)
      ? parsed.data.mood
      : null;

  let theme = THEMES.includes(parsed.data.theme as (typeof THEMES)[number])
    ? parsed.data.theme!
    : "dream";
  if (product.sku === "SEND_DROP" && mood) {
    theme = moodToTheme(mood);
  }

  const media = {
    ...(parsed.data.media || {}),
    ...(product.sku === "SEND_DROP"
      ? { kind: "drop", mood: mood || "secret" }
      : {}),
  };

  const db = await getDb();
  await db.prepare(
    `INSERT INTO gifts (
      id, token, sender_id, recipient_id, recipient_label, type, status,
      price_cents, currency, message, media_json, theme, music,
      anonymous, anonymous_id, reveal_enabled, reveal_status,
      open_when_label, unlock_at, opened_at, expires_at, created_at, easter_clicks
    ) VALUES (?, ?, ?, NULL, ?, ?, 'awaiting_payment', ?, 'eur', ?, ?, ?, NULL,
      ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 0)`
  ).run(
    id,
    token,
    user.id,
    sanitizeText(parsed.data.recipientLabel || "", 80) || null,
    product.sku,
    product.amountCents,
    sanitizeText(parsed.data.message),
    JSON.stringify(media),
    theme,
    isAnon ? 1 : 0,
    anonymousId,
    parsed.data.revealEnabled === false ? 0 : 1,
    isAnon ? "available" : "hidden",
    parsed.data.openWhenLabel ? sanitizeText(parsed.data.openWhenLabel, 120) : null,
    parsed.data.unlockAt || null,
    now
  );

  const orderId = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO orders (
      id, user_id, gift_id, gift_type, amount_cents, currency,
      stripe_session_id, stripe_payment_id, status, anonymous, reveal_status,
      metadata_json, created_at, paid_at
    ) VALUES (?, ?, ?, ?, ?, 'eur', NULL, NULL, 'pending', ?, ?, ?, ?, NULL)`
  ).run(
    orderId,
    user.id,
    id,
    product.sku,
    product.amountCents,
    isAnon ? 1 : 0,
    isAnon ? "available" : "hidden",
    JSON.stringify({
      snapshotPrice: product.amountCents,
      recipientLabel: parsed.data.recipientLabel || null,
      recipientPublic: generateRecipientLabel(),
    }),
    now
  );

  await track("gift_create_completed", { giftId: id, type: product.sku, anonymous: isAnon });
  const gift = (await db.prepare("SELECT * FROM gifts WHERE id = ?").get(id)) as unknown as GiftRow;
  return json({ gift, orderId }, 201);
}
