import crypto from "crypto";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { generateRecipientLabel } from "@/lib/anon-id";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";
import type { AnonIdentityRow, ChatThreadRow, GiftRow } from "@/lib/types";

export async function GET(
  req: Request,
  ctx: { params: Promise<{ token: string }> }
) {
  const { token } = await ctx.params;
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`open_get:${ip}`, 60, 60 * 1000);
  if (!rl.ok) return err("Easy — too many attempts. Wait a bit.", 429);

  const db = await getDb();
  const gift = (await db
    .prepare("SELECT * FROM gifts WHERE token = ?")
    .get(token)) as GiftRow | undefined;
  if (!gift) return err("Looks like this gift got lost. Try the link again.", 404);

  if (!["paid", "sent", "opened", "replied"].includes(gift.status)) {
    return err("This gift is not ready yet.", 402, "unpaid");
  }

  if (gift.unlock_at && Date.parse(gift.unlock_at) > Date.now()) {
    return json({
      locked: true,
      unlockAt: gift.unlock_at,
      openWhenLabel: gift.open_when_label,
      theme: gift.theme,
      type: gift.type,
    });
  }

  let publicAnonId: string | null = null;
  let revealStatus = gift.reveal_status;
  let revealedName: string | null = null;

  if (gift.anonymous && gift.anonymous_id) {
    const anon = (await db
      .prepare("SELECT * FROM anon_identities WHERE id = ?")
      .get(gift.anonymous_id)) as AnonIdentityRow | undefined;
    publicAnonId = anon?.public_anon_id ?? null;
    if (anon?.is_revealed) {
      revealStatus = "revealed";
      const sender = gift.sender_id
        ? ((await db
            .prepare("SELECT display_name FROM users WHERE id = ?")
            .get(gift.sender_id)) as { display_name: string } | undefined)
        : null;
      revealedName = sender?.display_name ?? null;
    }
  }

  let media: Record<string, unknown> = {};
  try {
    media = JSON.parse(gift.media_json || "{}") as Record<string, unknown>;
  } catch {
    media = {};
  }

  const engageRaw =
    media.engage && typeof media.engage === "object"
      ? (media.engage as {
          hintRequest?: { status?: string };
          revealRequest?: { status?: string };
          senderHint?: string | null;
        })
      : null;
  const hintStatus = engageRaw?.hintRequest?.status || "none";
  const engage = {
    hintRequest: hintStatus,
    revealRequest: engageRaw?.revealRequest?.status || "none",
    senderHint: hintStatus === "answered" ? engageRaw?.senderHint || null : null,
  };

  // Public media: strip engage internals; expose only safe clue + answered hint
  const publicMedia = { ...media };
  delete publicMedia.engage;
  if (engage.senderHint) {
    (publicMedia as { engageHint?: string }).engageHint = engage.senderHint;
  }

  return json({
    locked: false,
    paidBySender: true,
    gift: {
      id: gift.id,
      type: gift.type,
      theme: gift.theme,
      message: gift.message,
      status: gift.status,
      anonymous: Boolean(gift.anonymous),
      publicAnonId,
      revealStatus,
      revealedName,
      openWhenLabel: gift.open_when_label,
      openedAt: gift.opened_at,
      easterClicks: gift.easter_clicks,
      recipientLabel: gift.recipient_label,
      media: publicMedia,
      engage,
    },
  });
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ token: string }> }
) {
  const { token } = await ctx.params;
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`open_post:${ip}`, 40, 60 * 1000);
  if (!rl.ok) return err("Easy — too many attempts. Wait a bit.", 429);

  const db = await getDb();
  const gift = (await db
    .prepare("SELECT * FROM gifts WHERE token = ?")
    .get(token)) as GiftRow | undefined;
  if (!gift) return err("Looks like this gift got lost.", 404);
  if (!["paid", "sent", "opened", "replied"].includes(gift.status)) {
    return err("This gift is not ready yet.", 402);
  }
  if (gift.unlock_at && Date.parse(gift.unlock_at) > Date.now()) {
    return err("Not yet. This one is still locked.", 423);
  }

  let body: { action?: string; message?: string } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }

  const user = await getSessionUser();
  const action = body.action || "open";

  if (action === "easter") {
    await db.prepare("UPDATE gifts SET easter_clicks = easter_clicks + 1 WHERE id = ?").run(gift.id);
    const clicks = (
      (await db.prepare("SELECT easter_clicks FROM gifts WHERE id = ?").get(gift.id)) as {
        easter_clicks: number;
      }
    ).easter_clicks;
    let tip: string | null = null;
    if (clicks === 3) tip = "hey";
    if (clicks === 5) tip = "liked";
    return json({ clicks, tip });
  }

  if (action === "open") {
    if (!gift.opened_at) {
      await db.prepare(
        `UPDATE gifts SET status = 'opened', opened_at = ?, recipient_id = COALESCE(recipient_id, ?) WHERE id = ?`
      ).run(new Date().toISOString(), user?.id ?? null, gift.id);
      if (gift.sender_id) {
        await db.prepare(
          `INSERT INTO notifications (id, user_id, type, title, body, href, read_at, created_at)
           VALUES (?, ?, 'gift_opened', ?, ?, ?, NULL, ?)`
        ).run(
          crypto.randomUUID(),
          gift.sender_id,
          "They opened it. 👀",
          "Your moment was opened.",
          `/dashboard`,
          new Date().toISOString()
        );
      }
      await track("gift_opened", { giftId: gift.id, type: gift.type });
    }
    return json({ ok: true, openedFast: Boolean(gift.opened_at === null) });
  }

  if (action === "reply") {
    const message = sanitizeText(body.message || "", 2000);
    if (!message) return err("Write something first.", 400);
    const rl2 = await checkRateLimit(`reply:${gift.id}:${ip}`, 20, 60 * 60 * 1000);
    if (!rl2.ok) return err("Too many replies.", 429);

    if (user?.id && !gift.recipient_id && gift.sender_id !== user.id) {
      await db.prepare("UPDATE gifts SET recipient_id = ? WHERE id = ?").run(user.id, gift.id);
      gift.recipient_id = user.id;
    }

    let thread = (await db
      .prepare("SELECT * FROM chat_threads WHERE gift_id = ?")
      .get(gift.id)) as unknown as ChatThreadRow | undefined;

    if (!thread) {
      let senderLabel = "SENDER";
      if (gift.anonymous && gift.anonymous_id) {
        const anon = (await db
          .prepare("SELECT public_anon_id FROM anon_identities WHERE id = ?")
          .get(gift.anonymous_id)) as { public_anon_id: string } | undefined;
        senderLabel = anon?.public_anon_id || "ANON";
      }
      const meta = (await db
        .prepare("SELECT metadata_json FROM orders WHERE gift_id = ? ORDER BY created_at ASC LIMIT 1")
        .get(gift.id)) as { metadata_json: string } | undefined;
      let recipientLabel = generateRecipientLabel();
      try {
        const m = JSON.parse(meta?.metadata_json || "{}");
        if (m.recipientPublic) recipientLabel = m.recipientPublic;
      } catch {
        /* ignore */
      }
      const threadId = crypto.randomUUID();
      await db.prepare(
        `INSERT INTO chat_threads (id, gift_id, anon_identity_id, sender_label, recipient_label, created_at)
         VALUES (?, ?, ?, ?, ?, ?)`
      ).run(
        threadId,
        gift.id,
        gift.anonymous_id,
        senderLabel,
        recipientLabel,
        new Date().toISOString()
      );
      thread = (await db
        .prepare("SELECT * FROM chat_threads WHERE id = ?")
        .get(threadId)) as unknown as ChatThreadRow;
    }

    await db.prepare(
      `INSERT INTO chat_messages (id, thread_id, sender_side, body, created_at, read_at)
       VALUES (?, ?, 'recipient', ?, ?, NULL)`
    ).run(crypto.randomUUID(), thread.id, message, new Date().toISOString());
    await db.prepare(`UPDATE gifts SET status = 'replied' WHERE id = ?`).run(gift.id);

    if (gift.sender_id) {
      await db.prepare(
        `INSERT INTO notifications (id, user_id, type, title, body, href, read_at, created_at)
         VALUES (?, ?, 'gift_replied', ?, ?, ?, NULL, ?)`
      ).run(
        crypto.randomUUID(),
        gift.sender_id,
        "They replied. 💬",
        message.slice(0, 120),
        gift.anonymous ? `/engage/${gift.id}` : `/chat/${thread.id}`,
        new Date().toISOString()
      );
    }
    await track("gift_replied", { giftId: gift.id });
    return json({ ok: true, threadId: thread.id });
  }

  return err("Unknown action", 400);
}
