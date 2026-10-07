import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { checkRateLimit } from "@/lib/rate-limit";
import type { ChatMessageRow, ChatThreadRow, GiftRow } from "@/lib/types";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  const db = await getDb();
  const thread = (await db
    .prepare("SELECT * FROM chat_threads WHERE id = ?")
    .get(id)) as ChatThreadRow | undefined;
  if (!thread) return err("Not found", 404);

  const gift = (await db
    .prepare("SELECT * FROM gifts WHERE id = ?")
    .get(thread.gift_id)) as GiftRow | undefined;
  if (!gift) return err("Not found", 404);

  const isSender = gift.sender_id === user.id;
  const isRecipient = gift.recipient_id === user.id;
  if (!isSender && !isRecipient && user.role !== "admin") {
    return err("Forbidden", 403);
  }

  const blocked = (await db
    .prepare(
      `SELECT id FROM blocks WHERE blocker_id = ? AND blocked_key IN (?, ?)`
    )
    .get(user.id, gift.anonymous_id || "", gift.sender_id || ""));

  const messages = (await db
    .prepare(
      `SELECT id, sender_side, body, created_at, read_at FROM chat_messages
       WHERE thread_id = ? ORDER BY created_at ASC LIMIT 500`
    )
    .all(id)) as unknown as ChatMessageRow[];

  return json({
    thread: {
      id: thread.id,
      senderLabel: thread.sender_label,
      recipientLabel: thread.recipient_label,
      giftId: thread.gift_id,
      blocked: Boolean(blocked),
    },
    messages: messages.map((m) => ({
      id: m.id,
      side: m.sender_side,
      body: m.body,
      createdAt: m.created_at,
    })),
    me: isSender ? "anon" : "recipient",
  });
}

const postSchema = z.object({
  message: z.string().min(1).max(2000),
});

export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  const rl = await checkRateLimit(`chat:${user.id}`, 60, 60 * 60 * 1000);
  if (!rl.ok) return err("Too many messages.", 429);

  const db = await getDb();
  const thread = (await db
    .prepare("SELECT * FROM chat_threads WHERE id = ?")
    .get(id)) as ChatThreadRow | undefined;
  if (!thread) return err("Not found", 404);
  const gift = (await db
    .prepare("SELECT * FROM gifts WHERE id = ?")
    .get(thread.gift_id)) as GiftRow | undefined;
  if (!gift) return err("Not found", 404);

  const isSender = gift.sender_id === user.id;
  const isRecipient = gift.recipient_id === user.id;
  if (!isSender && !isRecipient) return err("Forbidden", 403);

  const blocked = (await db
    .prepare(
      `SELECT id FROM blocks WHERE (blocker_id = ? AND blocked_key IN (?, ?))
       OR (blocker_id = ? AND blocked_key = ?)`
    )
    .get(
      user.id,
      gift.anonymous_id || "",
      gift.sender_id || "",
      gift.sender_id || "",
      user.id
    ));
  if (blocked) return err("This conversation is blocked.", 403);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = postSchema.safeParse(body);
  if (!parsed.success) return err("Invalid message", 400);

  const side = isSender ? "anon" : "recipient";
  const msgId = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO chat_messages (id, thread_id, sender_side, body, created_at, read_at)
     VALUES (?, ?, ?, ?, ?, NULL)`
  ).run(msgId, id, side, sanitizeText(parsed.data.message), new Date().toISOString());

  return json({ id: msgId, side, body: sanitizeText(parsed.data.message) }, 201);
}
