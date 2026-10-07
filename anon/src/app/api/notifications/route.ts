import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const db = await getDb();
  const items = (await db
    .prepare(
      `SELECT id, type, title, body, href, read_at, created_at
       FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50`
    )
    .all(user.id));
  return json({ items });
}

export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  let body: { ids?: string[] } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  const db = await getDb();
  if (body.ids?.length) {
    const stmt = db.prepare(
      `UPDATE notifications SET read_at = ? WHERE user_id = ? AND id = ?`
    );
    const now = new Date().toISOString();
    for (const nid of body.ids) {
      await stmt.run(now, user.id, nid);
    }
  } else {
    await db.prepare(
      `UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL`
    ).run(new Date().toISOString(), user.id);
  }
  return json({ ok: true });
}
