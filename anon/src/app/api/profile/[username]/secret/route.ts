import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { createAnonIdentity, generatePublicAnonId, secureGiftToken } from "@/lib/anon-id";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { getProduct } from "@/lib/pricing";
import { getUserByUsername } from "@/lib/profile";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";

const schema = z.object({
  message: z.string().min(1).max(2000),
  kind: z
    .enum(["secret", "confession", "admirer", "question", "compliment", "mystery"])
    .optional(),
  clue: z.string().max(120).optional(),
  theme: z.string().max(32).optional(),
});

/** Free secret to a public profile — guest OK. No Stripe. */
export async function POST(
  req: Request,
  ctx: { params: Promise<{ username: string }> }
) {
  const { username } = await ctx.params;
  const recipient = await getUserByUsername(username);
  if (!recipient) return err("Profile not found", 404);

  const dbAllow = await getDb();
  const allow = (
    (await dbAllow
      .prepare(`SELECT COALESCE(allow_anon,1) as a FROM users WHERE id = ?`)
      .get(recipient.id)) as { a: number }
  ).a;
  if (!allow) return err("This person is not accepting anonymous messages.", 403);

  const sender = await getSessionUser();
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(
    `secret:${sender?.id || ip}:${recipient.id}`,
    12,
    60 * 60 * 1000
  );
  if (!rl.ok) return err("Slow down.", 429);

  if (sender?.id === recipient.id) {
    return err("You can't send a secret to yourself.", 400);
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid secret", 400);

  const product = getProduct("SEND_SECRET");
  const db = await getDb();
  const id = crypto.randomUUID();
  const token = secureGiftToken();
  const now = new Date().toISOString();

  let anonymousId: string | null = null;
  let guestLabel: string | null = null;
  if (sender) {
    anonymousId = (await createAnonIdentity(sender.id)).id;
  } else {
    guestLabel = generatePublicAnonId();
  }

  const media = {
    kind: "secret",
    secretKind: parsed.data.kind || "secret",
    clue: parsed.data.clue ? sanitizeText(parsed.data.clue, 120) : null,
    guestLabel,
  };

  await db.prepare(
    `INSERT INTO gifts (
      id, token, sender_id, recipient_id, recipient_label, type, status,
      price_cents, currency, message, media_json, theme, music,
      anonymous, anonymous_id, reveal_enabled, reveal_status,
      open_when_label, unlock_at, opened_at, expires_at, created_at, easter_clicks
    ) VALUES (?, ?, ?, ?, ?, 'SEND_SECRET', 'sent', 0, 'eur', ?, ?, ?, NULL,
      1, ?, 1, 'available', NULL, NULL, NULL, NULL, ?, 0)`
  ).run(
    id,
    token,
    sender?.id || null,
    recipient.id,
    recipient.display_name,
    sanitizeText(parsed.data.message),
    JSON.stringify(media),
    parsed.data.theme || "secret",
    anonymousId,
    now
  );

  await db.prepare(
    `INSERT INTO notifications (id, user_id, type, title, body, href, read_at, created_at)
     VALUES (?, ?, ?, ?, ?, ?, NULL, ?)`
  ).run(
    crypto.randomUUID(),
    recipient.id,
    "secret_received",
    "Someone left you a secret",
    "Open it when you're ready.",
    `/open/${token}`,
    now
  );

  await track("secret_sent", {
    giftId: id,
    recipientId: recipient.id,
    guest: !sender,
    kind: media.secretKind,
  });

  return json(
    {
      ok: true,
      token,
      openPath: `/open/${token}`,
      free: true,
      product: product?.sku || "SEND_SECRET",
      amountCents: product?.amountCents ?? 0,
    },
    201
  );
}
