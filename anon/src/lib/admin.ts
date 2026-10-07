import crypto from "crypto";
import { getSessionUser } from "@/lib/auth";
import { getDb } from "@/lib/db";
import type { UserRow } from "@/lib/types";

export type AdminRole = "owner" | "admin" | "moderator" | "support" | "analyst";

const STAFF: AdminRole[] = ["owner", "admin", "moderator", "support", "analyst"];

export function isStaffRole(role: string | null | undefined): role is AdminRole {
  return !!role && STAFF.includes(role as AdminRole);
}

export function adminEmail(): string | null {
  const e = process.env.ANON_ADMIN_EMAIL?.toLowerCase().trim();
  return e || null;
}

/** Promote configured owner email if present (login / session bootstrap). */
export async function ensureOwnerPromotion(user: UserRow): Promise<UserRow> {
  const email = adminEmail();
  if (!email || user.email.toLowerCase() !== email) return user;
  if (user.role === "owner") return user;
  const db = await getDb();
  await db.prepare(`UPDATE users SET role = 'owner' WHERE id = ?`).run(user.id);
  return { ...user, role: "owner" };
}

export function canAccessMissionControl(role: string): boolean {
  return isStaffRole(role);
}

export function canManageUsers(role: string): boolean {
  return role === "owner" || role === "admin" || role === "support";
}

export function canModerate(role: string): boolean {
  return role === "owner" || role === "admin" || role === "moderator";
}

export function canManageProducts(role: string): boolean {
  return role === "owner" || role === "admin";
}

export function canViewRevenue(role: string): boolean {
  return role === "owner" || role === "admin" || role === "analyst";
}

export async function requireStaff(): Promise<UserRow | null> {
  const user = await getSessionUser();
  if (!user) return null;
  const promoted = await ensureOwnerPromotion(user);
  if (!canAccessMissionControl(promoted.role)) return null;
  return promoted;
}

export async function writeAudit(opts: {
  adminId: string;
  action: string;
  targetType?: string;
  targetId?: string;
  metadata?: Record<string, unknown>;
}) {
  const db = await getDb();
  await db.prepare(
    `INSERT INTO admin_audit (id, admin_id, action, target_type, target_id, metadata_json, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).run(
    crypto.randomUUID(),
    opts.adminId,
    opts.action,
    opts.targetType || null,
    opts.targetId || null,
    JSON.stringify(opts.metadata || {}),
    new Date().toISOString()
  );
}
