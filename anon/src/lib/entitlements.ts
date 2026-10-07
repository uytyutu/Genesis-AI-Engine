import { getDb } from "@/lib/db";

export const FREE_BOT_LIMIT = 2;
export const PREMIUM_BOT_LIMIT = 8;

export type EntitlementKey = "ai_party" | "smart_bots" | "anon_plus";

export async function ensureEntitlementsTable() {
  const db = await getDb();
  await db.exec(`
    CREATE TABLE IF NOT EXISTS user_entitlements (
      user_id TEXT NOT NULL,
      key TEXT NOT NULL,
      source_sku TEXT,
      created_at TEXT NOT NULL,
      PRIMARY KEY (user_id, key)
    );
  `);
}

export async function grantEntitlement(userId: string, key: EntitlementKey, sourceSku?: string) {
  await ensureEntitlementsTable();
  const db = await getDb();
  await db
    .prepare(
      `INSERT INTO user_entitlements (user_id, key, source_sku, created_at)
       VALUES (?, ?, ?, ?)
       ON CONFLICT(user_id, key) DO UPDATE SET source_sku = excluded.source_sku`
    )
    .run(userId, key, sourceSku || null, new Date().toISOString());
}

export async function hasEntitlement(
  userId: string | null | undefined,
  key: EntitlementKey
): Promise<boolean> {
  if (!userId) return false;
  await ensureEntitlementsTable();
  const db = await getDb();
  const row = await db
    .prepare(`SELECT key FROM user_entitlements WHERE user_id = ? AND key = ?`)
    .get(userId, key);
  if (row) return true;
  if (key !== "anon_plus") {
    const plus = await db
      .prepare(`SELECT key FROM user_entitlements WHERE user_id = ? AND key = 'anon_plus'`)
      .get(userId);
    if (plus) return true;
  }
  return false;
}

export async function listEntitlements(userId: string): Promise<EntitlementKey[]> {
  await ensureEntitlementsTable();
  const db = await getDb();
  const rows = (await db
    .prepare(`SELECT key FROM user_entitlements WHERE user_id = ?`)
    .all(userId)) as { key: EntitlementKey }[];
  return rows.map((r) => r.key);
}

export async function botLimitForUser(userId: string | null | undefined): Promise<number> {
  if ((await hasEntitlement(userId, "ai_party")) || (await hasEntitlement(userId, "anon_plus"))) {
    return PREMIUM_BOT_LIMIT;
  }
  return FREE_BOT_LIMIT;
}

export async function canUseHardBots(userId: string | null | undefined): Promise<boolean> {
  return (
    (await hasEntitlement(userId, "smart_bots")) || (await hasEntitlement(userId, "anon_plus"))
  );
}

/** Map paid pack SKUs → entitlements */
export function entitlementsForSku(sku: string): EntitlementKey[] {
  switch (sku) {
    case "PACK_AI_PARTY":
      return ["ai_party"];
    case "PACK_SMART_BOTS":
      return ["smart_bots"];
    case "PACK_ANON_PLUS":
      return ["anon_plus", "ai_party", "smart_bots"];
    case "PACK_PARTY":
      return ["ai_party"];
    default:
      return [];
  }
}
