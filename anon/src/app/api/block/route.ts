import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

const schema = z.object({
  blockedKey: z.string().min(1).max(80),
});

export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid block", 400);

  const db = await getDb();
  const id = crypto.randomUUID();
  try {
    await db.prepare(
      `INSERT INTO blocks (id, blocker_id, blocked_key, created_at) VALUES (?, ?, ?, ?)`
    ).run(id, user.id, sanitizeText(parsed.data.blockedKey, 80), new Date().toISOString());
  } catch {
    return json({ ok: true, already: true });
  }
  return json({ id }, 201);
}
