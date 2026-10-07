import { canManageProducts, requireStaff, writeAudit } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { z } from "zod";

export async function GET() {
  const staff = await requireStaff();
  if (!staff) return err("Forbidden", 403);
  const db = await getDb();
  const flags = await db
    .prepare(`SELECT key, enabled, rollout, updated_at, updated_by FROM feature_flags ORDER BY key`)
    .all();
  return json({ flags });
}

const schema = z.object({
  key: z.string().min(2).max(64),
  enabled: z.boolean(),
  rollout: z.number().int().min(0).max(100).optional(),
});

export async function PATCH(req: Request) {
  const staff = await requireStaff();
  if (!staff || !canManageProducts(staff.role)) return err("Forbidden", 403);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid flag", 400);

  const db = await getDb();
  const now = new Date().toISOString();
  await db.prepare(
    `UPDATE feature_flags SET enabled = ?, rollout = COALESCE(?, rollout), updated_at = ?, updated_by = ?
     WHERE key = ?`
  ).run(
    parsed.data.enabled ? 1 : 0,
    parsed.data.rollout ?? null,
    now,
    staff.id,
    parsed.data.key
  );

  await writeAudit({
    adminId: staff.id,
    action: "flag.update",
    targetType: "feature_flag",
    targetId: parsed.data.key,
    metadata: { enabled: parsed.data.enabled, rollout: parsed.data.rollout },
  });

  return json({ ok: true });
}
