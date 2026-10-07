import { ensureOwnerPromotion } from "@/lib/admin";
import { getSessionUser, publicUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const promoted = await ensureOwnerPromotion(user);
  const db = await getDb();
  await db
    .prepare(`UPDATE users SET last_seen_at = ? WHERE id = ?`)
    .run(new Date().toISOString(), promoted.id);
  return json({ user: publicUser(promoted) });
}
