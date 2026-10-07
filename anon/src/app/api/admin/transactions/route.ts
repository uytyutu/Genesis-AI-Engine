import { canViewRevenue, requireStaff } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

export async function GET() {
  const staff = await requireStaff();
  if (!staff || !canViewRevenue(staff.role)) return err("Forbidden", 403);

  const db = await getDb();
  const orders = (await db
    .prepare(
      `SELECT o.id, o.user_id, o.gift_type, o.amount_cents, o.currency, o.status,
              o.stripe_session_id, o.stripe_payment_id, o.created_at, o.paid_at,
              u.email as user_email, u.username as user_username
       FROM orders o
       LEFT JOIN users u ON u.id = o.user_id
       ORDER BY o.created_at DESC LIMIT 100`
    )
    .all());

  return json({
    transactions: orders.map((o) => ({
      ...(o as object),
      provider: (o as { stripe_payment_id?: string }).stripe_payment_id ? "stripe" : "unknown",
    })),
    wallet: { supported: false, message: "Not supported" },
  });
}
