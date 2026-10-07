/**
 * Dev helper: reset password for ANON_ADMIN_EMAIL (default admin@anon.app).
 * Usage: node scripts/reset_owner_password.mjs [password]
 */
import crypto from "crypto";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, "..", "data", "anon.sqlite");
const email = (process.env.ANON_ADMIN_EMAIL || "admin@anon.app").toLowerCase().trim();
const password = process.argv[2] || "AnonOwner2026!";

const salt = crypto.randomBytes(16).toString("hex");
const hash = crypto.pbkdf2Sync(password, salt, 120_000, 32, "sha256").toString("hex");
const stored = `pbkdf2$${salt}$${hash}`;

const db = new Database(dbPath);
const row = db.prepare("SELECT id, email, role FROM users WHERE email = ?").get(email);
if (!row) {
  console.error("No user for", email, "— register that email first.");
  process.exit(1);
}
db.prepare("UPDATE users SET password_hash = ?, role = 'owner' WHERE email = ?").run(stored, email);
console.log("OK owner reset:", email, "role=owner");
console.log("Password:", password);
