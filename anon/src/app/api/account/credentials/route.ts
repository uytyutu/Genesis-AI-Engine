import { z } from "zod";
import {
  getSessionUser,
  hashPassword,
  sanitizeText,
  setSessionCookie,
  issueToken,
  verifyPassword,
} from "@/lib/auth";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import type { UserRow } from "@/lib/types";

/**
 * Email / password change — ONLY by the signed-in user, with current password.
 * Nothing in the system may change password or email automatically.
 */
const schema = z.object({
  currentPassword: z.string().min(1).max(128),
  newEmail: z.string().email().max(200).optional(),
  newPassword: z.string().min(8).max(128).optional(),
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
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Check current password and new values.", 400);
  if (!parsed.data.newEmail && !parsed.data.newPassword) {
    return err("Nothing to change.", 400);
  }

  if (!verifyPassword(parsed.data.currentPassword, user.password_hash)) {
    return err("Current password is wrong.", 401);
  }

  const db = await getDb();
  let email = user.email;
  let passwordHash = user.password_hash;

  if (parsed.data.newEmail) {
    const next = parsed.data.newEmail.toLowerCase().trim();
    if (next !== user.email) {
      const taken = await db.prepare("SELECT id FROM users WHERE email = ? AND id != ?").get(next, user.id);
      if (taken) return err("This email is already used.", 409);
      email = next;
      await db.prepare(`UPDATE users SET email = ? WHERE id = ?`).run(email, user.id);
    }
  }

  if (parsed.data.newPassword) {
    passwordHash = hashPassword(parsed.data.newPassword);
    await db.prepare(`UPDATE users SET password_hash = ? WHERE id = ?`).run(passwordHash, user.id);
  }

  const updated = (await db
    .prepare("SELECT * FROM users WHERE id = ?")
    .get(user.id)) as unknown as UserRow;

  // Refresh sealed session snapshot so cold-start rehydrate keeps the new credentials.
  await setSessionCookie(issueToken(updated.id), updated);

  return json({
    ok: true,
    email: sanitizeText(updated.email, 200),
    passwordChanged: Boolean(parsed.data.newPassword),
    emailChanged: Boolean(parsed.data.newEmail && parsed.data.newEmail.toLowerCase() !== user.email),
  });
}
