import crypto from "crypto";
import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { checkRateLimit } from "@/lib/rate-limit";

const schema = z.object({
  targetType: z.enum(["gift", "user", "message", "anon"]),
  targetId: z.string().min(1).max(80),
  reason: z.string().min(3).max(1000),
});

export async function POST(req: Request) {
  const user = await getSessionUser();
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`report:${user?.id || ip}`, 10, 60 * 60 * 1000);
  if (!rl.ok) return err("Too many reports.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid report", 400);

  const db = await getDb();
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO reports (id, reporter_id, target_type, target_id, reason, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'open', ?)`
  ).run(
    id,
    user?.id ?? null,
    parsed.data.targetType,
    sanitizeText(parsed.data.targetId, 80),
    sanitizeText(parsed.data.reason, 1000),
    new Date().toISOString()
  );
  return json({ id }, 201);
}
