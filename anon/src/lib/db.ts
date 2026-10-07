import fs from "fs";
import path from "path";

const DATA_DIR = path.join(process.cwd(), "data");
const DB_PATH = path.join(DATA_DIR, "anon.sqlite");

export type AnonStatement = {
  get(...params: unknown[]): Promise<Record<string, unknown> | undefined>;
  all(...params: unknown[]): Promise<Record<string, unknown>[]>;
  run(...params: unknown[]): Promise<{ changes: number; lastInsertRowid?: number | bigint }>;
};

export type AnonDb = {
  prepare(sql: string): AnonStatement;
  exec(sql: string): Promise<void>;
};

let _db: AnonDb | null = null;
let _migrateDone = false;

function tursoConfig(): { url: string; authToken: string } | null {
  const url = process.env.TURSO_DATABASE_URL || process.env.LIBSQL_URL;
  if (!url) return null;
  const authToken =
    process.env.TURSO_AUTH_TOKEN || process.env.LIBSQL_AUTH_TOKEN || "";
  return { url, authToken };
}

function libsqlRow(row: unknown, columns: string[]): Record<string, unknown> {
  if (row == null) return {};
  if (typeof row === "object" && !Array.isArray(row)) {
    const r = row as Record<string, unknown>;
    if (columns.length && columns[0] in r) {
      const out: Record<string, unknown> = {};
      for (const c of columns) out[c] = r[c];
      return out;
    }
  }
  const arr = row as unknown[];
  const out: Record<string, unknown> = {};
  columns.forEach((c, i) => {
    out[c] = arr[i];
  });
  return out;
}

async function createLibsqlDb(url: string, authToken?: string): Promise<AnonDb> {
  const { createClient } = await import("@libsql/client");
  const client = createClient({
    url,
    ...(authToken ? { authToken } : {}),
  });

  const db: AnonDb = {
    prepare(sql: string): AnonStatement {
      return {
        async get(...params: unknown[]) {
          const result = await client.execute({ sql, args: params as never[] });
          if (!result.rows.length) return undefined;
          return libsqlRow(result.rows[0], result.columns);
        },
        async all(...params: unknown[]) {
          const result = await client.execute({ sql, args: params as never[] });
          return result.rows.map((r) => libsqlRow(r, result.columns));
        },
        async run(...params: unknown[]) {
          const result = await client.execute({ sql, args: params as never[] });
          return {
            changes: result.rowsAffected ?? 0,
            lastInsertRowid: result.lastInsertRowid,
          };
        },
      };
    },
    async exec(sql: string) {
      await client.executeMultiple(sql);
    },
  };
  return db;
}

async function createLocalDb(): Promise<AnonDb> {
  const Database = (await import("better-sqlite3")).default;
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  const native = new Database(DB_PATH);
  native.pragma("journal_mode = WAL");
  native.pragma("foreign_keys = ON");

  const db: AnonDb = {
    prepare(sql: string): AnonStatement {
      const stmt = native.prepare(sql);
      return {
        async get(...params: unknown[]) {
          return stmt.get(...params) as Record<string, unknown> | undefined;
        },
        async all(...params: unknown[]) {
          return stmt.all(...params) as Record<string, unknown>[];
        },
        async run(...params: unknown[]) {
          const info = stmt.run(...params);
          return { changes: info.changes, lastInsertRowid: info.lastInsertRowid };
        },
      };
    },
    async exec(sql: string) {
      native.exec(sql);
    },
  };
  return db;
}

const MIGRATE_CORE = `
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      display_name TEXT NOT NULL,
      username TEXT UNIQUE,
      avatar TEXT,
      language TEXT NOT NULL DEFAULT 'en',
      timezone TEXT NOT NULL DEFAULT 'UTC',
      role TEXT NOT NULL DEFAULT 'user',
      created_at TEXT NOT NULL,
      banned_at TEXT
    );

    CREATE TABLE IF NOT EXISTS anon_identities (
      id TEXT PRIMARY KEY,
      public_anon_id TEXT NOT NULL UNIQUE,
      owner_user_id TEXT NOT NULL,
      is_revealed INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      FOREIGN KEY(owner_user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS gifts (
      id TEXT PRIMARY KEY,
      token TEXT NOT NULL UNIQUE,
      sender_id TEXT,
      recipient_id TEXT,
      recipient_label TEXT,
      type TEXT NOT NULL,
      status TEXT NOT NULL,
      price_cents INTEGER NOT NULL,
      currency TEXT NOT NULL DEFAULT 'eur',
      message TEXT NOT NULL DEFAULT '',
      media_json TEXT NOT NULL DEFAULT '{}',
      theme TEXT NOT NULL DEFAULT 'dream',
      music TEXT,
      anonymous INTEGER NOT NULL DEFAULT 0,
      anonymous_id TEXT,
      reveal_enabled INTEGER NOT NULL DEFAULT 1,
      reveal_status TEXT NOT NULL DEFAULT 'hidden',
      open_when_label TEXT,
      unlock_at TEXT,
      opened_at TEXT,
      expires_at TEXT,
      created_at TEXT NOT NULL,
      easter_clicks INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(sender_id) REFERENCES users(id),
      FOREIGN KEY(anonymous_id) REFERENCES anon_identities(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY,
      user_id TEXT,
      gift_id TEXT,
      gift_type TEXT NOT NULL,
      amount_cents INTEGER NOT NULL,
      currency TEXT NOT NULL DEFAULT 'eur',
      stripe_session_id TEXT,
      stripe_payment_id TEXT,
      status TEXT NOT NULL,
      anonymous INTEGER NOT NULL DEFAULT 0,
      reveal_status TEXT NOT NULL DEFAULT 'hidden',
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL,
      paid_at TEXT,
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(gift_id) REFERENCES gifts(id)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_stripe_session
      ON orders(stripe_session_id) WHERE stripe_session_id IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_stripe_payment
      ON orders(stripe_payment_id) WHERE stripe_payment_id IS NOT NULL;

    CREATE TABLE IF NOT EXISTS processed_webhooks (
      event_id TEXT PRIMARY KEY,
      processed_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS chat_threads (
      id TEXT PRIMARY KEY,
      gift_id TEXT NOT NULL,
      anon_identity_id TEXT,
      sender_label TEXT NOT NULL,
      recipient_label TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(gift_id) REFERENCES gifts(id)
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
      id TEXT PRIMARY KEY,
      thread_id TEXT NOT NULL,
      sender_side TEXT NOT NULL,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL,
      read_at TEXT,
      FOREIGN KEY(thread_id) REFERENCES chat_threads(id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      type TEXT NOT NULL,
      title TEXT NOT NULL,
      body TEXT NOT NULL,
      href TEXT,
      read_at TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS reports (
      id TEXT PRIMARY KEY,
      reporter_id TEXT,
      target_type TEXT NOT NULL,
      target_id TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'open',
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS blocks (
      id TEXT PRIMARY KEY,
      blocker_id TEXT NOT NULL,
      blocked_key TEXT NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE(blocker_id, blocked_key)
    );

    CREATE TABLE IF NOT EXISTS analytics_events (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      props_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rate_limits (
      key TEXT PRIMARY KEY,
      count INTEGER NOT NULL,
      window_start TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS game_rooms (
      id TEXT PRIMARY KEY,
      code TEXT NOT NULL UNIQUE,
      mode_id TEXT NOT NULL,
      host_id TEXT,
      status TEXT NOT NULL,
      phase TEXT NOT NULL,
      max_players INTEGER NOT NULL,
      state_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS game_players (
      id TEXT PRIMARY KEY,
      room_id TEXT NOT NULL,
      user_id TEXT,
      display_label TEXT NOT NULL,
      seat INTEGER NOT NULL,
      score INTEGER NOT NULL DEFAULT 0,
      joined_at TEXT NOT NULL,
      UNIQUE(room_id, seat),
      FOREIGN KEY(room_id) REFERENCES game_rooms(id)
    );

    CREATE TABLE IF NOT EXISTS user_ranks (
      user_id TEXT PRIMARY KEY,
      xp INTEGER NOT NULL DEFAULT 0,
      league TEXT NOT NULL DEFAULT 'bronze',
      wins INTEGER NOT NULL DEFAULT 0,
      games INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL
    );
  `;

const MIGRATE_ADMIN = `
    CREATE TABLE IF NOT EXISTS admin_audit (
      id TEXT PRIMARY KEY,
      admin_id TEXT NOT NULL,
      action TEXT NOT NULL,
      target_type TEXT,
      target_id TEXT,
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL,
      FOREIGN KEY(admin_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS feature_flags (
      key TEXT PRIMARY KEY,
      enabled INTEGER NOT NULL DEFAULT 1,
      rollout INTEGER NOT NULL DEFAULT 100,
      updated_at TEXT NOT NULL,
      updated_by TEXT
    );

    CREATE TABLE IF NOT EXISTS product_overrides (
      sku TEXT PRIMARY KEY,
      active INTEGER NOT NULL DEFAULT 1,
      amount_cents INTEGER,
      updated_at TEXT NOT NULL,
      updated_by TEXT
    );
  `;

const ALTER_USER_COLUMNS = [
  `ALTER TABLE users ADD COLUMN bio TEXT NOT NULL DEFAULT ''`,
  `ALTER TABLE users ADD COLUMN profile_theme TEXT NOT NULL DEFAULT 'secret'`,
  `ALTER TABLE users ADD COLUMN allow_anon INTEGER NOT NULL DEFAULT 1`,
  `ALTER TABLE users ADD COLUMN last_seen_at TEXT`,
];

async function migrateAlterColumn(db: AnonDb, sql: string) {
  try {
    await db.exec(sql);
  } catch {
    /* column exists */
  }
}

export async function migrate(db: AnonDb): Promise<void> {
  await db.exec(MIGRATE_CORE);

  for (const sql of ALTER_USER_COLUMNS) {
    await migrateAlterColumn(db, sql);
  }

  await db.exec(MIGRATE_ADMIN);

  const flagDefaults: Array<[string, number]> = [
    ["ANONYMOUS_MESSAGES", 1],
    ["SECRET_ADMIRER", 1],
    ["GUESS_WHO", 1],
    ["MUTUAL_REVEAL", 1],
    ["ANONYMOUS_VOICE", 0],
    ["MOMENTS", 1],
    ["OPEN_LATER", 1],
    ["SECRET_CHAIN", 0],
    ["VOICE_ROOMS", 0],
    ["GAMES", 1],
    ["ANON_PLUS", 1],
    ["TELEGRAM_STARS", 0],
    ["VIRAL_LOOPS", 1],
  ];
  const now = new Date().toISOString();
  const flagIns = db.prepare(
    `INSERT OR IGNORE INTO feature_flags (key, enabled, rollout, updated_at) VALUES (?, ?, 100, ?)`
  );
  for (const [key, enabled] of flagDefaults) {
    await flagIns.run(key, enabled, now);
  }

  await db.exec(`
    CREATE TABLE IF NOT EXISTS viral_spaces (
      id TEXT PRIMARY KEY,
      code TEXT NOT NULL UNIQUE,
      kind TEXT NOT NULL,
      owner_id TEXT,
      title TEXT NOT NULL,
      config_json TEXT NOT NULL DEFAULT '{}',
      unlocked INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_viral_spaces_owner ON viral_spaces(owner_id);
    CREATE TABLE IF NOT EXISTS viral_answers (
      id TEXT PRIMARY KEY,
      space_id TEXT NOT NULL,
      side TEXT NOT NULL DEFAULT 'guest',
      payload_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL,
      FOREIGN KEY(space_id) REFERENCES viral_spaces(id)
    );
    CREATE INDEX IF NOT EXISTS idx_viral_answers_space ON viral_answers(space_id);
  `);
}

export async function getDb(): Promise<AnonDb> {
  if (_db && _migrateDone) return _db;
  if (!_db) {
    const turso = tursoConfig();
    if (turso) {
      _db = await createLibsqlDb(turso.url, turso.authToken);
    } else if (process.env.VERCEL) {
      // Ephemeral until Turso is linked — keeps Mission Control bootable on Vercel.
      _db = await createLibsqlDb(":memory:");
    } else {
      _db = await createLocalDb();
    }
  }
  if (!_migrateDone) {
    await migrate(_db);
    await bootstrapOwnerIfNeeded(_db);
    _migrateDone = true;
  }
  return _db;
}

async function bootstrapOwnerIfNeeded(db: AnonDb) {
  const email = (process.env.ANON_ADMIN_EMAIL || "").toLowerCase().trim();
  const password = (process.env.ANON_BOOTSTRAP_PASSWORD || "").trim();
  if (!email || !password) return;
  const existing = await db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) {
    await db.prepare(`UPDATE users SET role = 'owner' WHERE email = ?`).run(email);
    return;
  }
  const crypto = await import("crypto");
  const id = crypto.randomUUID();
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.pbkdf2Sync(password, salt, 120_000, 32, "sha256").toString("hex");
  const stored = `pbkdf2$${salt}$${hash}`;
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO users (id, email, password_hash, display_name, username, language, timezone, role, created_at)
       VALUES (?, ?, ?, ?, ?, 'en', 'UTC', 'owner', ?)`
    )
    .run(id, email, stored, "ANON Owner", "anon_owner", now);
}
