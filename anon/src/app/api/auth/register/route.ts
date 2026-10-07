import crypto from "crypto";
import { z } from "zod";
import { hashPassword, issueToken, publicUser, sanitizeText, setSessionCookie } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";
import { suggestUsername } from "@/lib/profile";

const schema = z.object({
  email: z.string().email().max(200),
  password: z.string().min(8).max(128),
  displayName: z.string().min(1).max(80),
  language: z.string().max(8).optional(),
  username: z.string().min(3).max(24).optional(),
});

export async function POST(req: Request) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`register:${ip}`, 8, 60 * 60 * 1000);
  if (!rl.ok) return err("Easy — too many attempts. Wait a bit.", 429, "rate_limited");

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Check email, password (8+), and name.", 400);

  const email = parsed.data.email.toLowerCase().trim();
  const displayName = sanitizeText(parsed.data.displayName, 80);
  const db = await getDb();
  const existing = await db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) return err("An account with this email already exists.", 409);

  const adminEmail = process.env.ANON_ADMIN_EMAIL?.toLowerCase().trim();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  let username = parsed.data.username
    ? parsed.data.username.toLowerCase().replace(/^@/, "")
    : await suggestUsername(displayName);
  const taken = await db.prepare("SELECT id FROM users WHERE username = ?").get(username);
  if (taken) username = await suggestUsername(displayName);

  await db.prepare(
    `INSERT INTO users (id, email, password_hash, display_name, username, language, timezone, role, created_at)
     VALUES (?, ?, ?, ?, ?, ?, 'UTC', ?, ?)`
  ).run(
    id,
    email,
    hashPassword(parsed.data.password),
    displayName,
    username,
    parsed.data.language || "en",
    adminEmail && email === adminEmail ? "owner" : "user",
    now
  );

  const user = (await db.prepare("SELECT * FROM users WHERE id = ?").get(id)) as unknown as import("@/lib/types").UserRow;
  const token = issueToken(id);
  await setSessionCookie(token, user);
  await track("user_registered", { userId: id });
  return json({ user: publicUser(user) }, 201);
}
