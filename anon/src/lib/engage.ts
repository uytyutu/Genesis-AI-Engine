import crypto from "crypto";
import { getDb } from "./db";
import type { GiftRow } from "./types";

export type EngageStatus = "none" | "pending" | "answered" | "declined" | "accepted";

export type EngageState = {
  hintRequest?: {
    status: EngageStatus;
    requestedAt?: string;
    requesterId?: string;
    orderId?: string;
  };
  revealRequest?: {
    status: EngageStatus;
    requestedAt?: string;
    requesterId?: string;
    orderId?: string;
  };
  /** Voluntary clue from sender — never system-generated private data */
  senderHint?: string | null;
};

export function parseMedia(raw: string | null | undefined): Record<string, unknown> {
  try {
    return JSON.parse(raw || "{}") as Record<string, unknown>;
  } catch {
    return {};
  }
}

export function getEngage(media: Record<string, unknown>): EngageState {
  const e = media.engage;
  if (!e || typeof e !== "object") return {};
  return e as EngageState;
}

export function setEngage(media: Record<string, unknown>, engage: EngageState): string {
  return JSON.stringify({ ...media, engage });
}

export async function notifyUser(opts: {
  userId: string;
  type: string;
  title: string;
  body: string;
  href: string;
}) {
  const db = await getDb();
  await db.prepare(
    `INSERT INTO notifications (id, user_id, type, title, body, href, read_at, created_at)
     VALUES (?, ?, ?, ?, ?, ?, NULL, ?)`
  ).run(
    crypto.randomUUID(),
    opts.userId,
    opts.type,
    opts.title,
    opts.body,
    opts.href,
    new Date().toISOString()
  );
}

/** After ASK_HINT / ASK_REVEAL payment — mark request pending + notify sender. */
export async function fulfillEngageOrder(order: {
  id: string;
  gift_id: string | null;
  gift_type: string;
  user_id: string | null;
}): Promise<void> {
  if (!order.gift_id || !order.user_id) return;
  if (order.gift_type !== "ASK_HINT" && order.gift_type !== "ASK_REVEAL") return;

  const db = await getDb();
  const gift = (await db.prepare("SELECT * FROM gifts WHERE id = ?").get(order.gift_id)) as
    | GiftRow
    | undefined;
  if (!gift?.sender_id) return;

  const media = parseMedia(gift.media_json);
  const engage = getEngage(media);
  const now = new Date().toISOString();

  if (order.gift_type === "ASK_HINT") {
    engage.hintRequest = {
      status: "pending",
      requestedAt: now,
      requesterId: order.user_id,
      orderId: order.id,
    };
  } else {
    engage.revealRequest = {
      status: "pending",
      requestedAt: now,
      requesterId: order.user_id,
      orderId: order.id,
    };
  }

  await db.prepare("UPDATE gifts SET media_json = ? WHERE id = ?").run(
    setEngage(media, engage),
    gift.id
  );

  if (order.gift_type === "ASK_HINT") {
    await notifyUser({
      userId: gift.sender_id,
      type: "hint_requested",
      title: "They want a clue",
      body: "You can send a voluntary hint — or stay fully anonymous.",
      href: `/engage/${gift.id}`,
    });
  } else {
    await notifyUser({
      userId: gift.sender_id,
      type: "reveal_requested",
      title: "They asked who you are",
      body: "Stay anonymous, or agree to reveal — your choice.",
      href: `/engage/${gift.id}`,
    });
  }
}

export function isEngageSku(sku: string): boolean {
  return sku === "ASK_HINT" || sku === "ASK_REVEAL";
}
