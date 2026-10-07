import { requireStaff } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

export async function GET() {
  const staff = await requireStaff();
  if (!staff || (staff.role !== "owner" && staff.role !== "admin")) {
    return err("Forbidden", 403);
  }

  const db = await getDb();
  const rows = await db
    .prepare(
      `SELECT a.id, a.action, a.target_type, a.target_id, a.metadata_json, a.created_at,
              u.email as admin_email, u.display_name as admin_name
       FROM admin_audit a
       LEFT JOIN users u ON u.id = a.admin_id
       ORDER BY a.created_at DESC LIMIT 100`
    )
    .all();

  return json({ audit: rows });
}
