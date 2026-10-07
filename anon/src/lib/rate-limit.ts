import { getDb } from "./db";

/** Simple sliding window stored in SQLite — abuse protection foundation. */
export async function checkRateLimit(
  key: string,
  limit: number,
  windowMs: number
): Promise<{ ok: boolean; remaining: number }> {
  const db = await getDb();
  const now = Date.now();
  const row = (await db
    .prepare("SELECT count, window_start FROM rate_limits WHERE key = ?")
    .get(key)) as { count: number; window_start: string } | undefined;

  if (!row) {
    await db.prepare(
      "INSERT INTO rate_limits (key, count, window_start) VALUES (?, 1, ?)"
    ).run(key, new Date(now).toISOString());
    return { ok: true, remaining: limit - 1 };
  }

  const start = Date.parse(row.window_start);
  if (!Number.isFinite(start) || now - start > windowMs) {
    await db.prepare(
      "UPDATE rate_limits SET count = 1, window_start = ? WHERE key = ?"
    ).run(new Date(now).toISOString(), key);
    return { ok: true, remaining: limit - 1 };
  }

  if (row.count >= limit) {
    return { ok: false, remaining: 0 };
  }

  await db.prepare("UPDATE rate_limits SET count = count + 1 WHERE key = ?").run(key);
  return { ok: true, remaining: limit - row.count - 1 };
}
