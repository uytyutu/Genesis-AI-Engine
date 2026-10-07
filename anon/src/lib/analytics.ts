import crypto from "crypto";
import { getDb } from "./db";

/** Provider-agnostic analytics — swap sinks later without rewriting calls. */
export async function track(name: string, props: Record<string, unknown> = {}) {
  try {
    const db = await getDb();
    await db.prepare(
      `INSERT INTO analytics_events (id, name, props_json, created_at) VALUES (?, ?, ?, ?)`
    ).run(
      crypto.randomUUID(),
      name,
      JSON.stringify(props),
      new Date().toISOString()
    );
  } catch {
    // never break UX for analytics
  }
}
