import { canManageUsers, requireStaff, writeAudit } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { z } from "zod";

export async function GET(req: Request) {
  const staff = await requireStaff();
  if (!staff) return err("Forbidden", 403);

  const url = new URL(req.url);
  const q = (url.searchParams.get("q") || "").trim().toLowerCase();
  const filter = url.searchParams.get("filter") || "all";

  const db = await getDb();
  let rows = (await db
    .prepare(
      `SELECT id, email, display_name, username, role, created_at, last_seen_at, banned_at,
              COALESCE(bio,'') as bio, COALESCE(allow_anon,1) as allow_anon
       FROM users ORDER BY created_at DESC LIMIT 200`
    )
    .all()) as Array<Record<string, unknown>>;

  if (q) {
    rows = rows.filter((u) => {
      const hay = `${u.email} ${u.username || ""} ${u.display_name} ${u.id}`.toLowerCase();
      return hay.includes(q);
    });
  }
  if (filter === "blocked") rows = rows.filter((u) => !!u.banned_at);
  if (filter === "active") rows = rows.filter((u) => !u.banned_at);
  if (filter === "staff") {
    rows = rows.filter((u) =>
      ["owner", "admin", "moderator", "support", "analyst"].includes(String(u.role))
    );
  }
  if (filter === "new") {
    const week = Date.now() - 7 * 864e5;
    rows = rows.filter((u) => Date.parse(String(u.created_at)) >= week);
  }

  const enriched = await Promise.all(
    rows.map(async (u) => {
      const id = String(u.id);
      const secretsIn = (
        (await db
          .prepare(
            `SELECT COUNT(*) as c FROM gifts WHERE recipient_id = ? AND (type = 'SEND_SECRET' OR anonymous = 1)`
          )
          .get(id)) as { c: number }
      ).c;
      const purchases = (
        (await db
          .prepare(`SELECT COUNT(*) as c FROM orders WHERE user_id = ? AND status = 'paid'`)
          .get(id)) as { c: number }
      ).c;
      const reports = (
        (await db
          .prepare(
            `SELECT COUNT(*) as c FROM reports WHERE target_id = ? OR reporter_id = ?`
          )
          .get(id, id)) as { c: number }
      ).c;
      return { ...u, secretsIn, purchases, reports };
    })
  );

  return json({ users: enriched });
}

const patchSchema = z.object({
  userId: z.string().min(1),
  action: z.enum(["suspend", "restore", "block", "unblock"]),
  reason: z.string().max(200).optional(),
});

export async function PATCH(req: Request) {
  const staff = await requireStaff();
  if (!staff || !canManageUsers(staff.role)) return err("Forbidden", 403);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) return err("Invalid action", 400);

  const db = await getDb();
  const target = (await db
    .prepare(`SELECT id, role, email FROM users WHERE id = ?`)
    .get(parsed.data.userId)) as { id: string; role: string; email: string } | undefined;
  if (!target) return err("User not found", 404);
  if (target.role === "owner" && staff.role !== "owner") {
    return err("Cannot modify owner", 403);
  }
  if (target.id === staff.id && parsed.data.action !== "restore") {
    return err("Cannot suspend yourself", 400);
  }

  const now = new Date().toISOString();
  if (parsed.data.action === "suspend" || parsed.data.action === "block") {
    await db.prepare(`UPDATE users SET banned_at = ? WHERE id = ?`).run(now, target.id);
  } else {
    await db.prepare(`UPDATE users SET banned_at = NULL WHERE id = ?`).run(target.id);
  }

  await writeAudit({
    adminId: staff.id,
    action: `user.${parsed.data.action}`,
    targetType: "user",
    targetId: target.id,
    metadata: { reason: parsed.data.reason || null, email: target.email },
  });

  return json({ ok: true });
}
