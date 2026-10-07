import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import type { GiftRow } from "@/lib/types";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const db = await getDb();
  const gift = await db.prepare("SELECT * FROM gifts WHERE id = ?").get(id) as GiftRow | undefined;
  if (!gift) return err("Not found", 404);
  if (gift.sender_id !== user.id && gift.recipient_id !== user.id && user.role !== "admin") {
    return err("Forbidden", 403);
  }
  return json({ gift: publicGift(gift, user.id === gift.sender_id || user.role === "admin") });
}

function publicGift(gift: GiftRow, includeToken: boolean) {
  return {
    id: gift.id,
    token: includeToken && ["paid", "sent", "opened", "replied"].includes(gift.status)
      ? gift.token
      : undefined,
    type: gift.type,
    status: gift.status,
    priceCents: gift.price_cents,
    currency: gift.currency,
    message: ["opened", "replied"].includes(gift.status) || includeToken ? gift.message : null,
    theme: gift.theme,
    anonymous: Boolean(gift.anonymous),
    revealStatus: gift.reveal_status,
    openWhenLabel: gift.open_when_label,
    unlockAt: gift.unlock_at,
    openedAt: gift.opened_at,
    createdAt: gift.created_at,
    recipientLabel: gift.recipient_label,
  };
}
