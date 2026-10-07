import crypto from "crypto";
import { getDb } from "./db";

/** Public-facing Anonymous ID only — never expose owner user id. */
export function generatePublicAnonId(): string {
  const n = crypto.randomInt(10_000, 99_999);
  return `ANON #${n}`;
}

export function generateRecipientLabel(): string {
  const n = crypto.randomInt(10_000, 99_999);
  return `RECIPIENT #${n}`;
}

export async function createAnonIdentity(ownerUserId: string): Promise<{
  id: string;
  publicAnonId: string;
}> {
  const db = await getDb();
  for (let i = 0; i < 8; i++) {
    const id = crypto.randomUUID();
    const publicAnonId = generatePublicAnonId();
    try {
      const result = await db.prepare(
        `INSERT INTO anon_identities (id, public_anon_id, owner_user_id, is_revealed, created_at)
         VALUES (?, ?, ?, 0, ?)`
      ).run(id, publicAnonId, ownerUserId, new Date().toISOString());
      if (result.changes > 0) return { id, publicAnonId };
    } catch {
      // unique collision — retry
    }
  }
  throw new Error("Could not allocate anonymous identity");
}

export function secureGiftToken(): string {
  return crypto.randomBytes(24).toString("base64url");
}
