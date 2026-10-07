import crypto from "crypto";
import { cookies } from "next/headers";
import { getDb } from "./db";
import type { UserRow } from "./types";

const COOKIE = "anon_session";
const SNAP_COOKIE = "anon_snap";
const TOKEN_TTL_SEC = 60 * 60 * 24 * 30;

function authSecret(): string {
  const s = process.env.ANON_AUTH_SECRET?.trim();
  if (!s) {
    if (process.env.NODE_ENV === "production") {
      throw new Error("ANON_AUTH_SECRET is required in production");
    }
    return "dev-only-anon-auth-secret-change-me";
  }
  return s;
}

export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.pbkdf2Sync(password, salt, 120_000, 32, "sha256").toString("hex");
  return `pbkdf2$${salt}$${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const parts = stored.split("$");
  if (parts.length !== 3 || parts[0] !== "pbkdf2") return false;
  const [, salt, hash] = parts;
  const next = crypto.pbkdf2Sync(password, salt, 120_000, 32, "sha256").toString("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(hash, "hex"), Buffer.from(next, "hex"));
  } catch {
    return false;
  }
}

function sign(payload: string): string {
  return crypto.createHmac("sha256", authSecret()).update(payload).digest("base64url");
}

export function issueToken(userId: string): string {
  const exp = Math.floor(Date.now() / 1000) + TOKEN_TTL_SEC;
  const body = `${userId}.${exp}`;
  return `${body}.${sign(body)}`;
}

export function decodeToken(token: string): { userId: string } | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [userId, expStr, sig] = parts;
  const body = `${userId}.${expStr}`;
  const expected = sign(body);
  try {
    if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  } catch {
    return null;
  }
  const exp = Number(expStr);
  if (!Number.isFinite(exp) || exp < Math.floor(Date.now() / 1000)) return null;
  return { userId };
}

function cookieSecure(): boolean {
  const publicUrl = (process.env.ANON_PUBLIC_URL || "").trim();
  return process.env.NODE_ENV === "production" || publicUrl.startsWith("https://");
}

function sessionCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: cookieSecure(),
    sameSite: "lax" as const,
    path: "/",
    maxAge,
  };
}

/** Compact user snapshot so Vercel cold starts can rehydrate after :memory: wipe. */
type SnapUser = {
  id: string;
  email: string;
  password_hash: string;
  display_name: string;
  username: string | null;
  avatar: string | null;
  language: string;
  timezone: string;
  role: UserRow["role"];
  created_at: string;
};

function sealSnap(user: UserRow): string {
  const snap: SnapUser = {
    id: user.id,
    email: user.email,
    password_hash: user.password_hash,
    display_name: user.display_name,
    username: user.username,
    avatar: user.avatar,
    language: user.language,
    timezone: user.timezone,
    role: user.role,
    created_at: user.created_at,
  };
  const body = Buffer.from(JSON.stringify(snap), "utf8").toString("base64url");
  return `${body}.${sign(body)}`;
}

function unsealSnap(raw: string): SnapUser | null {
  const i = raw.lastIndexOf(".");
  if (i < 1) return null;
  const body = raw.slice(0, i);
  const sig = raw.slice(i + 1);
  const expected = sign(body);
  try {
    if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  } catch {
    return null;
  }
  try {
    const snap = JSON.parse(Buffer.from(body, "base64url").toString("utf8")) as SnapUser;
    if (!snap?.id || !snap?.email || !snap?.password_hash) return null;
    return snap;
  } catch {
    return null;
  }
}

async function upsertSnapUser(snap: SnapUser): Promise<UserRow> {
  const db = await getDb();
  const existing = (await db
    .prepare("SELECT * FROM users WHERE id = ?")
    .get(snap.id)) as UserRow | undefined;
  // Never overwrite password/email from a snapshot if the user already exists.
  if (existing) return existing;
  await db
    .prepare(
      `INSERT OR IGNORE INTO users
        (id, email, password_hash, display_name, username, avatar, language, timezone, role, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      snap.id,
      snap.email,
      snap.password_hash,
      snap.display_name,
      snap.username,
      snap.avatar,
      snap.language || "en",
      snap.timezone || "UTC",
      snap.role || "user",
      snap.created_at
    );
  const row = (await db
    .prepare("SELECT * FROM users WHERE id = ?")
    .get(snap.id)) as UserRow | undefined;
  if (row) return row;
  // email collision after memory reset — keep session identity
  return {
    id: snap.id,
    email: snap.email,
    password_hash: snap.password_hash,
    display_name: snap.display_name,
    username: snap.username,
    avatar: snap.avatar,
    language: snap.language || "en",
    timezone: snap.timezone || "UTC",
    role: snap.role || "user",
    created_at: snap.created_at,
    banned_at: null,
  };
}

export async function setSessionCookie(token: string, user?: UserRow) {
  const jar = await cookies();
  const opts = sessionCookieOptions(TOKEN_TTL_SEC);
  jar.set(COOKIE, token, opts);
  if (user) {
    jar.set(SNAP_COOKIE, sealSnap(user), opts);
  }
}

export async function clearSessionCookie() {
  const jar = await cookies();
  const opts = sessionCookieOptions(0);
  jar.set(COOKIE, "", opts);
  jar.set(SNAP_COOKIE, "", opts);
}

async function promoteOwnerIfNeeded(user: UserRow): Promise<UserRow> {
  const email = process.env.ANON_ADMIN_EMAIL?.toLowerCase().trim();
  if (!email || user.email.toLowerCase() !== email) return user;
  if (user.role === "owner") return user;
  const db = await getDb();
  await db.prepare(`UPDATE users SET role = 'owner' WHERE id = ?`).run(user.id);
  return { ...user, role: "owner" as UserRow["role"] };
}

export async function getSessionUser(): Promise<UserRow | null> {
  const jar = await cookies();
  const token = jar.get(COOKIE)?.value;
  if (!token) return null;
  const decoded = decodeToken(token);
  if (!decoded) return null;
  const db = await getDb();
  let user = (await db
    .prepare("SELECT * FROM users WHERE id = ? AND banned_at IS NULL")
    .get(decoded.userId)) as UserRow | undefined;

  if (!user) {
    const snapRaw = jar.get(SNAP_COOKIE)?.value;
    if (snapRaw) {
      const snap = unsealSnap(snapRaw);
      if (snap && snap.id === decoded.userId) {
        user = await upsertSnapUser(snap);
      }
    }
  }

  if (!user || user.banned_at) return null;
  return promoteOwnerIfNeeded(user);
}

export function publicUser(u: UserRow) {
  return {
    id: u.id,
    email: u.email,
    displayName: u.display_name,
    username: u.username,
    avatar: u.avatar,
    language: u.language,
    timezone: u.timezone,
    role: u.role,
    createdAt: u.created_at,
  };
}

export function sanitizeText(input: string, max = 4000): string {
  return input
    .replace(/[<>]/g, "")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .trim()
    .slice(0, max);
}
