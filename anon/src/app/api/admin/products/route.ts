import { canManageProducts, requireStaff, writeAudit } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";
import { PRODUCTS, type GiftSku } from "@/lib/pricing";
import { z } from "zod";

export async function GET() {
  const staff = await requireStaff();
  if (!staff || !canManageProducts(staff.role)) return err("Forbidden", 403);

  const db = await getDb();
  const overrides = (await db
    .prepare(`SELECT sku, active, amount_cents FROM product_overrides`)
    .all()) as Array<{ sku: string; active: number; amount_cents: number | null }>;
  const map = new Map(overrides.map((o) => [o.sku, o]));

  const products = Object.values(PRODUCTS).map((p) => {
    const o = map.get(p.sku);
    return {
      sku: p.sku,
      pillar: p.pillar,
      emoji: p.emoji,
      nameKey: p.nameKey,
      amountCents: o?.amount_cents ?? p.amountCents,
      catalogCents: p.amountCents,
      currency: p.currency,
      active: o ? o.active === 1 : true,
      impulse: p.impulse,
    };
  });

  return json({ products });
}

const schema = z.object({
  sku: z.string(),
  active: z.boolean().optional(),
  amountCents: z.number().int().min(0).max(100000).optional(),
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
  if (!parsed.success) return err("Invalid", 400);
  if (!PRODUCTS[parsed.data.sku as GiftSku]) return err("Unknown SKU", 404);

  const db = await getDb();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO product_overrides (sku, active, amount_cents, updated_at, updated_by)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(sku) DO UPDATE SET
       active = COALESCE(excluded.active, product_overrides.active),
       amount_cents = COALESCE(excluded.amount_cents, product_overrides.amount_cents),
       updated_at = excluded.updated_at,
       updated_by = excluded.updated_by`
  ).run(
    parsed.data.sku,
    parsed.data.active === undefined ? 1 : parsed.data.active ? 1 : 0,
    parsed.data.amountCents ?? null,
    now,
    staff.id
  );

  await writeAudit({
    adminId: staff.id,
    action: "product.update",
    targetType: "product",
    targetId: parsed.data.sku,
    metadata: parsed.data,
  });

  return json({ ok: true });
}
