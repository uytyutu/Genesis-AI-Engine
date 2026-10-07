import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { err, json } from "@/lib/api";
import { VIRAL_PRODUCTS, isViralKind, viralProductTitle, type ViralKind } from "@/lib/viral/catalog";
import { createViralSpace } from "@/lib/viral/store";
import { createCheckoutSession } from "@/lib/stripe";
import { getDb } from "@/lib/db";
import { getProduct } from "@/lib/pricing";

const PAID_CREATE: Partial<Record<ViralKind, string>> = {
  map: "VIRAL_MAP",
  say: "VIRAL_SAY",
  when: "VIRAL_WHEN",
  duo: "VIRAL_DUO",
};

const createSchema = z.object({
  kind: z.string(),
  title: z.string().max(120).optional(),
  config: z.record(z.string(), z.unknown()).optional(),
});

export async function GET() {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const db = await getDb();
  const rows = await db
    .prepare(
      `SELECT id, code, kind, title, unlocked, created_at FROM viral_spaces
       WHERE owner_id = ? ORDER BY created_at DESC LIMIT 40`
    )
    .all(user.id);
  return json({ spaces: rows });
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = createSchema.safeParse(body);
  if (!parsed.success) return err("Invalid payload", 400);
  if (!isViralKind(parsed.data.kind)) return err("Unknown loop", 400);

  const kind = parsed.data.kind;
  const user = await getSessionUser();
  const catalogKey =
    kind === "think"
      ? "VIRAL_THINK"
      : kind === "map"
        ? "VIRAL_MAP"
        : kind === "say"
          ? "VIRAL_SAY"
          : kind === "when"
            ? "VIRAL_WHEN"
            : kind === "words"
              ? "VIRAL_WORDS"
              : kind === "duo"
                ? "VIRAL_DUO"
                : kind === "ask"
                  ? "VIRAL_ASK"
                  : kind === "guess"
                    ? "VIRAL_GUESS_HINT"
                    : "VIRAL_FRAGMENT";
  const title = sanitizeText(parsed.data.title || viralProductTitle(catalogKey), 120);
  const paySku = PAID_CREATE[kind];

  if (kind === "guess") {
    return json({ redirect: "/secrets" });
  }

  if (!paySku) {
    // Free loops — login preferred for ownership, but ask/think/words/fragment can be owned when logged in
    const space = await createViralSpace({
      kind,
      ownerId: user?.id || null,
      title,
      config: parsed.data.config,
    });
    return json(
      {
        space: {
          id: space.id,
          code: space.code,
          kind: space.kind,
          title: space.title,
          path: `/v/${space.code}`,
          sharePath: `/s/${space.code}`,
        },
      },
      201
    );
  }

  if (!user) return err("Login required", 401);
  const product = getProduct(paySku);
  if (!product) return err("Product missing", 500);

  const db = await getDb();
  const orderId = crypto.randomUUID();
  const giftId = crypto.randomUUID();
  const token = crypto.randomBytes(12).toString("hex");
  const now = new Date().toISOString();
  const media = {
    viral: { kind, title, config: parsed.data.config || {} },
  };

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
      paySku,
      product.amountCents,
      title,
      JSON.stringify(media),
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
      paySku,
      product.amountCents,
      JSON.stringify({ viralKind: kind, viralTitle: title, viralConfig: parsed.data.config || {} }),
      now
    );

  const session = await createCheckoutSession({
    orderId,
    giftId,
    amountCents: product.amountCents,
    currency: "eur",
    label: title,
    successPath: `/orders/success?order_id=${orderId}&viral=1`,
    cancelPath: `/loops?cancelled=1`,
    metadata: { viral_kind: kind, viral_title: title },
  });

  return json({
    checkoutUrl: session.url,
    sessionId: session.sessionId,
    sandbox: session.sandbox,
    orderId,
  });
}
