import { z } from "zod";
import { ensureOwnerPromotion } from "@/lib/admin";
import { issueToken, publicUser, setSessionCookie, verifyPassword } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { checkRateLimit } from "@/lib/rate-limit";
import type { UserRow } from "@/lib/types";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1).max(128),
});

export async function POST(req: Request) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`login:${ip}`, 20, 15 * 60 * 1000);
  if (!rl.ok) return err("Easy — too many attempts. Wait a bit.", 429, "rate_limited");

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid credentials", 400);

  const db = await getDb();
  const user = (await db
    .prepare("SELECT * FROM users WHERE email = ?")
    .get(parsed.data.email.toLowerCase().trim())) as UserRow | undefined;

  if (!user || user.banned_at || !verifyPassword(parsed.data.password, user.password_hash)) {
    return err("Invalid email or password", 401);
  }

  const promoted = await ensureOwnerPromotion(user);
  await db
    .prepare(`UPDATE users SET last_seen_at = ? WHERE id = ?`)
    .run(new Date().toISOString(), promoted.id);

  await setSessionCookie(issueToken(promoted.id), promoted);
  return json({ user: publicUser(promoted) });
}
