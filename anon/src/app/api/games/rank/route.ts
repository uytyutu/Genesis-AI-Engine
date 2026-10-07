import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

export async function GET() {
  const user = await getSessionUser();
  const db = await getDb();
  const top = (await db
    .prepare(
      `SELECT u.display_name, r.xp, r.league, r.wins, r.games
       FROM user_ranks r
       JOIN users u ON u.id = r.user_id
       ORDER BY r.xp DESC LIMIT 20`
    )
    .all());
  let me = null;
  if (user) {
    me = await db
      .prepare("SELECT xp, league, wins, games FROM user_ranks WHERE user_id = ?")
      .get(user.id);
  }
  return json({ top, me });
}
