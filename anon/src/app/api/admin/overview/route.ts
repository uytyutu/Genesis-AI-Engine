import { requireStaff } from "@/lib/admin";
import { getDb } from "@/lib/db";
import { err, json } from "@/lib/api";

function dayStartIso() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

function monthStartIso() {
  const d = new Date();
  d.setDate(1);
  d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

export async function GET() {
  const staff = await requireStaff();
  if (!staff) return err("Forbidden — Mission Control requires staff role", 403);

  const db = await getDb();
  const today = dayStartIso();
  const month = monthStartIso();
  const onlineCutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString();

  const count = async (sql: string, ...params: unknown[]) =>
    ((await db.prepare(sql).get(...params)) as { c: number }).c;
  const sum = async (sql: string, ...params: unknown[]) =>
    ((await db.prepare(sql).get(...params)) as { s: number }).s;

  const totalUsers = await count("SELECT COUNT(*) AS c FROM users");
  const usersToday = await count("SELECT COUNT(*) AS c FROM users WHERE created_at >= ?", today);
  const onlineUsers = await count(
    "SELECT COUNT(*) AS c FROM users WHERE last_seen_at IS NOT NULL AND last_seen_at >= ?",
    onlineCutoff
  );
  const messagesToday = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE created_at >= ? AND status IN ('paid','sent','opened','replied')`,
    today
  );
  const anonToday = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE created_at >= ? AND (anonymous = 1 OR type IN ('SEND_SECRET','SEND_ANON'))`,
    today
  );
  const secretsTotal = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE type = 'SEND_SECRET' OR (anonymous = 1 AND type = 'SEND_ANON')`
  );
  const secretsOpened = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE opened_at IS NOT NULL AND (type = 'SEND_SECRET' OR anonymous = 1)`
  );
  const secretsReplied = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE status = 'replied' AND (type = 'SEND_SECRET' OR anonymous = 1)`
  );
  const momentsToday = await count(
    `SELECT COUNT(*) AS c FROM gifts WHERE created_at >= ? AND type LIKE '%MOMENT%'`,
    today
  );
  const activeRooms = await count(
    `SELECT COUNT(*) AS c FROM game_rooms WHERE status IN ('lobby','live','playing')`
  );
  const gamesPlayed = await count(`SELECT COUNT(*) AS c FROM game_rooms WHERE status = 'finished'`);
  const gamesToday = await count(
    `SELECT COUNT(*) AS c FROM game_rooms WHERE created_at >= ?`,
    today
  );
  const openReports = await count(`SELECT COUNT(*) AS c FROM reports WHERE status = 'open'`);
  const revenueToday = await sum(
    `SELECT COALESCE(SUM(amount_cents),0) AS s FROM orders WHERE status = 'paid' AND paid_at >= ?`,
    today
  );
  const revenueMonth = await sum(
    `SELECT COALESCE(SUM(amount_cents),0) AS s FROM orders WHERE status = 'paid' AND paid_at >= ?`,
    month
  );
  const paidOrders = await count(`SELECT COUNT(*) AS c FROM orders WHERE status = 'paid'`);
  const revenueTotal = await sum(
    `SELECT COALESCE(SUM(amount_cents),0) AS s FROM orders WHERE status = 'paid'`
  );
  const refunds = await sum(
    `SELECT COALESCE(SUM(amount_cents),0) AS s FROM orders WHERE status = 'refunded'`
  );

  const activity = (await db
    .prepare(
      `SELECT id, name, props_json, created_at FROM analytics_events
       ORDER BY created_at DESC LIMIT 40`
    )
    .all()) as Array<{ id: string; name: string; props_json: string; created_at: string }>;

  const recentUsers = (await db
    .prepare(
      `SELECT id, email, display_name, username, role, created_at, last_seen_at, banned_at
       FROM users ORDER BY created_at DESC LIMIT 12`
    )
    .all());

  return json({
    role: staff.role,
    kpis: {
      onlineUsers,
      usersToday,
      newUsers: usersToday,
      totalUsers,
      messagesToday,
      anonymousMessagesToday: anonToday,
      momentsToday,
      voiceMessages: 0,
      activeRooms,
      gamesPlayed,
      gamesToday,
      revenueTodayCents: revenueToday,
      revenueMonthCents: revenueMonth,
      revenueTotalCents: revenueTotal,
      refundsCents: refunds,
      paidOrders,
      openReports,
      secretsTotal,
      secretsOpened,
      secretsReplied,
      openRate: secretsTotal ? Math.round((secretsOpened / secretsTotal) * 100) : 0,
      replyRate: secretsOpened ? Math.round((secretsReplied / secretsOpened) * 100) : 0,
    },
    activity: activity.map((a) => {
      let props: Record<string, unknown> = {};
      try {
        props = JSON.parse(a.props_json || "{}") as Record<string, unknown>;
      } catch {
        props = {};
      }
      return {
        id: a.id,
        type: a.name,
        time: a.created_at,
        props,
      };
    }),
    recentUsers,
    note: {
      voiceMessages: "Not live — flag ANONYMOUS_VOICE off",
      wallet: "Not supported",
    },
  });
}
