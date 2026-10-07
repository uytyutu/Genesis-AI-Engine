import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { isValidUsername, normalizeUsername, suggestUsername } from "@/lib/profile";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);
  const db = await getDb();
  const row = (await db
    .prepare(
      `SELECT id, email, display_name, username, bio, profile_theme, allow_anon, created_at
       FROM users WHERE id = ?`
    )
    .get(user.id)) as {
    id: string;
    email: string;
    display_name: string;
    username: string | null;
    bio: string;
    profile_theme: string;
    allow_anon: number;
    created_at: string;
  };

  const secretsReceived = (
    (await db
      .prepare(
        `SELECT COUNT(*) as c FROM gifts WHERE recipient_id = ? AND status IN ('paid','sent','opened','replied')`
      )
      .get(user.id)) as { c: number }
  ).c;

  return json({
    profile: {
      id: row.id,
      email: row.email,
      displayName: row.display_name,
      username: row.username,
      bio: row.bio || "",
      theme: row.profile_theme || "secret",
      allowAnon: row.allow_anon !== 0,
      secretsReceived,
      sharePath: row.username ? `/@${row.username}` : null,
      createdAt: row.created_at,
      suggestedUsername: row.username ? null : await suggestUsername(row.display_name),
    },
  });
}

const patchSchema = z.object({
  username: z.string().min(3).max(24).optional(),
  bio: z.string().max(160).optional(),
  displayName: z.string().min(1).max(80).optional(),
  theme: z.string().max(32).optional(),
  allowAnon: z.boolean().optional(),
});

export async function PATCH(req: Request) {
  const user = await getSessionUser();
  if (!user) return err("Unauthorized", 401);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) return err("Invalid profile", 400);

  const db = await getDb();

  if (parsed.data.username != null) {
    const u = normalizeUsername(parsed.data.username);
    if (!isValidUsername(u)) {
      return err("Username: 3–24 chars, a-z 0-9 _", 400);
    }
    const taken = (await db
      .prepare(`SELECT id FROM users WHERE username = ? AND id != ?`)
      .get(u, user.id));
    if (taken) return err("Username taken", 409);
    await db.prepare(`UPDATE users SET username = ? WHERE id = ?`).run(u, user.id);
  }

  if (parsed.data.bio != null) {
    await db.prepare(`UPDATE users SET bio = ? WHERE id = ?`).run(
      sanitizeText(parsed.data.bio, 160),
      user.id
    );
  }
  if (parsed.data.displayName != null) {
    await db.prepare(`UPDATE users SET display_name = ? WHERE id = ?`).run(
      sanitizeText(parsed.data.displayName, 80),
      user.id
    );
  }
  if (parsed.data.theme != null) {
    await db.prepare(`UPDATE users SET profile_theme = ? WHERE id = ?`).run(
      sanitizeText(parsed.data.theme, 32),
      user.id
    );
  }
  if (parsed.data.allowAnon != null) {
    await db.prepare(`UPDATE users SET allow_anon = ? WHERE id = ?`).run(
      parsed.data.allowAnon ? 1 : 0,
      user.id
    );
  }

  return GET();
}
