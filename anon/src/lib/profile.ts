import { getDb } from "@/lib/db";
import type { UserRow } from "@/lib/types";

const USERNAME_RE = /^[a-z0-9_]{3,24}$/;

export function normalizeUsername(raw: string): string {
  return raw.trim().toLowerCase().replace(/^@/, "");
}

export function isValidUsername(raw: string): boolean {
  return USERNAME_RE.test(normalizeUsername(raw));
}

export async function suggestUsername(displayName: string): Promise<string> {
  const base = displayName
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 18);
  const seed = base || "anon";
  const db = await getDb();
  for (let i = 0; i < 20; i++) {
    const candidate = i === 0 ? seed : `${seed}${Math.floor(Math.random() * 900 + 100)}`;
    const taken = await db.prepare("SELECT id FROM users WHERE username = ?").get(candidate);
    if (!taken) return candidate;
  }
  return `anon_${Date.now().toString(36).slice(-6)}`;
}

export type PublicProfile = {
  username: string;
  displayName: string;
  bio: string;
  theme: string;
  allowAnon: boolean;
  secretsReceived: number;
  createdAt: string;
};

export async function getPublicProfile(username: string): Promise<PublicProfile | null> {
  const u = normalizeUsername(username);
  const db = await getDb();
  const row = (await db
    .prepare(
      `SELECT id, username, display_name, bio, profile_theme, allow_anon, created_at
       FROM users WHERE username = ? AND banned_at IS NULL`
    )
    .get(u)) as
    | (UserRow & { bio?: string; profile_theme?: string; allow_anon?: number })
    | undefined;
  if (!row?.username) return null;

  const secretsReceived = (
    (await db
      .prepare(
        `SELECT COUNT(*) as c FROM gifts
         WHERE recipient_id = ? AND status IN ('paid','sent','opened','replied')
           AND (anonymous = 1 OR type IN ('SEND_SECRET','SEND_ANON','SEND_DROP'))`
      )
      .get(row.id)) as { c: number }
  ).c;

  return {
    username: row.username,
    displayName: row.display_name,
    bio: (row as { bio?: string }).bio || "",
    theme: (row as { profile_theme?: string }).profile_theme || "secret",
    allowAnon: ((row as { allow_anon?: number }).allow_anon ?? 1) === 1,
    secretsReceived,
    createdAt: row.created_at,
  };
}

export async function getUserByUsername(username: string) {
  const u = normalizeUsername(username);
  const db = await getDb();
  return (await db
    .prepare(`SELECT * FROM users WHERE username = ? AND banned_at IS NULL`)
    .get(u)) as UserRow | undefined;
}
