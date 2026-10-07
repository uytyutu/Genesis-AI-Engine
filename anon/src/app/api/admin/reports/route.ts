import { canModerate, requireStaff, writeAudit } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { z } from "zod";

export async function GET(req: Request) {
  const staff = await requireStaff();
  if (!staff || !canModerate(staff.role)) return err("Forbidden", 403);

  const status = new URL(req.url).searchParams.get("status") || "open";
  const db = await getDb();
  const rows = (await db
    .prepare(
      `SELECT r.id, r.reporter_id, r.target_type, r.target_id, r.reason, r.status, r.created_at,
              u.email as reporter_email, u.username as reporter_username
       FROM reports r
       LEFT JOIN users u ON u.id = r.reporter_id
       WHERE (? = 'all' OR r.status = ?)
       ORDER BY r.created_at DESC LIMIT 100`
    )
    .all(status, status));

  return json({ reports: rows });
}

const patchSchema = z.object({
  reportId: z.string().min(1),
  action: z.enum(["resolve", "dismiss", "reviewing", "block_sender"]),
  note: z.string().max(300).optional(),
});

export async function PATCH(req: Request) {
  const staff = await requireStaff();
  if (!staff || !canModerate(staff.role)) return err("Forbidden", 403);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) return err("Invalid", 400);

  const db = await getDb();
  const report = (await db
    .prepare(`SELECT * FROM reports WHERE id = ?`)
    .get(parsed.data.reportId)) as
    | { id: string; target_type: string; target_id: string; status: string }
    | undefined;
  if (!report) return err("Report not found", 404);

  const nextStatus =
    parsed.data.action === "dismiss"
      ? "dismissed"
      : parsed.data.action === "reviewing"
        ? "reviewing"
        : "resolved";

  await db.prepare(`UPDATE reports SET status = ? WHERE id = ?`).run(nextStatus, report.id);

  if (parsed.data.action === "block_sender" && report.target_type === "user") {
    await db.prepare(`UPDATE users SET banned_at = ? WHERE id = ?`).run(
      new Date().toISOString(),
      report.target_id
    );
  }

  await writeAudit({
    adminId: staff.id,
    action: `report.${parsed.data.action}`,
    targetType: "report",
    targetId: report.id,
    metadata: { note: parsed.data.note || null, nextStatus },
  });

  return json({ ok: true, status: nextStatus });
}
