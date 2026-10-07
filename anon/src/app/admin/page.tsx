"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { formatMoney } from "@/lib/pricing";
import { useI18n } from "@/components/I18nProvider";

type Tab =
  | "dashboard"
  | "users"
  | "moderation"
  | "revenue"
  | "products"
  | "flags"
  | "health"
  | "audit";

type Kpis = Record<string, number>;
type Activity = { id: string; type: string; time: string; props: Record<string, unknown> };

function activityLabel(type: string): string {
  const map: Record<string, string> = {
    user_registered: "👤 New user registered",
    secret_sent: "💌 Anonymous message sent",
    gift_opened: "✨ Moment / gift opened",
    gift_created: "🎁 Gift created",
    payment_completed: "💳 Payment completed",
    report_created: "🚨 Report created",
  };
  return map[type] || `• ${type}`;
}

export default function MissionControlPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("dashboard");
  const [role, setRole] = useState("");
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [users, setUsers] = useState<Array<Record<string, unknown>>>([]);
  const [reports, setReports] = useState<Array<Record<string, unknown>>>([]);
  const [tx, setTx] = useState<Array<Record<string, unknown>>>([]);
  const [products, setProducts] = useState<Array<Record<string, unknown>>>([]);
  const [flags, setFlags] = useState<Array<Record<string, unknown>>>([]);
  const [health, setHealth] = useState<{
    overall: string;
    checks: Record<string, unknown>;
    note?: string;
  } | null>(null);
  const [audit, setAudit] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  const loadOverview = useCallback(async () => {
    const r = await fetch("/api/admin/overview");
    const d = await r.json();
    if (!r.ok) {
      setError(d.error || "Forbidden");
      return false;
    }
    setRole(d.role || "");
    setKpis(d.kpis);
    setActivity(d.activity || []);
    setError("");
    return true;
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await fetch("/api/auth/me");
        if (!me.ok) {
          setLoading(false);
          router.replace("/auth/login?next=/admin");
          return;
        }
        await loadOverview();
      } catch {
        setError("Could not reach Mission Control API.");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, loadOverview]);

  async function loadTab(next: Tab) {
    setTab(next);
    if (next === "users") {
      const r = await fetch(`/api/admin/users?q=${encodeURIComponent(q)}`);
      const d = await r.json();
      if (r.ok) setUsers(d.users || []);
    }
    if (next === "moderation") {
      const r = await fetch("/api/admin/reports?status=all");
      const d = await r.json();
      if (r.ok) setReports(d.reports || []);
    }
    if (next === "revenue") {
      const r = await fetch("/api/admin/transactions");
      const d = await r.json();
      if (r.ok) setTx(d.transactions || []);
    }
    if (next === "products") {
      const r = await fetch("/api/admin/products");
      const d = await r.json();
      if (r.ok) setProducts(d.products || []);
    }
    if (next === "flags") {
      const r = await fetch("/api/admin/flags");
      const d = await r.json();
      if (r.ok) setFlags(d.flags || []);
    }
    if (next === "health") {
      const r = await fetch("/api/admin/health");
      const d = await r.json();
      if (r.ok) setHealth(d);
    }
    if (next === "audit") {
      const r = await fetch("/api/admin/audit");
      const d = await r.json();
      if (r.ok) setAudit(d.audit || []);
    }
  }

  async function userAction(userId: string, action: "suspend" | "restore") {
    if (!confirm(`${action} this user?`)) return;
    await fetch("/api/admin/users", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId, action }),
    });
    loadTab("users");
  }

  async function reportAction(reportId: string, action: "resolve" | "dismiss") {
    await fetch("/api/admin/reports", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reportId, action }),
    });
    loadTab("moderation");
  }

  async function toggleFlag(key: string, enabled: boolean) {
    await fetch("/api/admin/flags", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, enabled: !enabled }),
    });
    loadTab("flags");
  }

  async function toggleProduct(sku: string, active: boolean) {
    if (!confirm(`Set ${sku} ${active ? "inactive" : "active"}?`)) return;
    await fetch("/api/admin/products", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sku, active: !active }),
    });
    loadTab("products");
  }

  if (loading) {
    return <main className="anon-card p-6 text-sm anon-muted">Loading Mission Control…</main>;
  }

  if (error) {
    return (
      <main className="anon-card mx-auto max-w-lg space-y-4 p-6">
        <h1 className="text-xl font-semibold">Mission Control</h1>
        <p className="text-sm text-amber-200">{error}</p>
        <p className="text-sm anon-muted">
          Root cause: staff role required. Login with the email from{" "}
          <code className="text-violet-200">ANON_ADMIN_EMAIL</code> (promoted to owner on
          login/session), or register that email first.
        </p>
        <div className="flex gap-2">
          <Link href="/auth/login?next=/admin" className="anon-btn anon-btn-primary">
            Log in
          </Link>
          <Link href="/auth/register?next=/admin" className="anon-btn anon-btn-ghost">
            Register owner
          </Link>
        </div>
      </main>
    );
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "dashboard", label: "Dashboard" },
    { id: "users", label: "Users" },
    { id: "moderation", label: "Moderation" },
    { id: "revenue", label: "Revenue" },
    { id: "products", label: "Products" },
    { id: "flags", label: "Flags" },
    { id: "health", label: "System" },
    { id: "audit", label: "Audit" },
  ];

  return (
    <main className="anim-in space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.3em] text-violet-300">ANON</p>
          <h1 className="mt-1 text-2xl font-semibold">Mission Control</h1>
          <p className="mt-1 text-sm anon-muted">
            {t("admin.sub")} · role: <span className="text-violet-200">{role}</span>
          </p>
        </div>
        <button
          type="button"
          className="anon-btn anon-btn-ghost text-xs"
          onClick={() => loadOverview()}
        >
          Refresh
        </button>
      </header>

      <nav className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
        {tabs.map((x) => (
          <button
            key={x.id}
            type="button"
            onClick={() => loadTab(x.id)}
            className={`rounded-xl px-3 py-1.5 text-xs ${
              tab === x.id ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/5"
            }`}
          >
            {x.label}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && kpis && (
        <>
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {[
              ["Online (15m)", kpis.onlineUsers],
              ["Users today", kpis.usersToday],
              ["Total users", kpis.totalUsers],
              ["Messages today", kpis.messagesToday],
              ["Anon today", kpis.anonymousMessagesToday],
              ["Moments today", kpis.momentsToday],
              ["Active rooms", kpis.activeRooms],
              ["Games today", kpis.gamesToday],
              ["Open reports", kpis.openReports],
              ["Revenue today", formatMoney(kpis.revenueTodayCents || 0)],
              ["Revenue month", formatMoney(kpis.revenueMonthCents || 0)],
              ["Secret open rate", `${kpis.openRate}%`],
              ["Secret reply rate", `${kpis.replyRate}%`],
              ["Voice msgs", "Not live"],
            ].map(([label, value]) => (
              <div key={String(label)} className="anon-card p-4">
                <div className="text-xs anon-muted">{label}</div>
                <div className="mt-2 text-xl font-semibold">{value}</div>
              </div>
            ))}
          </section>

          <section className="anon-card p-5">
            <h2 className="font-semibold">Live activity</h2>
            {activity.length === 0 ? (
              <p className="mt-3 text-sm anon-muted">No data yet.</p>
            ) : (
              <ul className="mt-3 max-h-80 space-y-2 overflow-y-auto text-sm">
                {activity.map((a) => (
                  <li
                    key={a.id}
                    className="flex justify-between gap-3 border-b border-white/5 py-2"
                  >
                    <span>{activityLabel(a.type)}</span>
                    <span className="shrink-0 text-xs anon-muted">
                      {new Date(a.time).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {tab === "users" && (
        <section className="space-y-3">
          <div className="flex gap-2">
            <input
              className="anon-input flex-1"
              placeholder="Search username / email / id"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <button type="button" className="anon-btn anon-btn-primary" onClick={() => loadTab("users")}>
              Search
            </button>
          </div>
          {users.length === 0 ? (
            <p className="text-sm anon-muted">No data yet.</p>
          ) : (
            users.map((u) => (
              <div key={String(u.id)} className="anon-card flex flex-wrap items-center justify-between gap-3 p-4">
                <div>
                  <p className="font-medium">
                    @{String(u.username || "—")} · {String(u.display_name)}
                  </p>
                  <p className="text-xs anon-muted">
                    {String(u.email)} · {String(u.role)} · secrets {String(u.secretsIn)} · purchases{" "}
                    {String(u.purchases)}
                    {u.banned_at ? " · SUSPENDED" : ""}
                  </p>
                </div>
                <div className="flex gap-2">
                  {u.username ? (
                    <Link href={`/@${u.username}`} className="anon-btn anon-btn-ghost text-xs">
                      Profile
                    </Link>
                  ) : null}
                  <button
                    type="button"
                    className="anon-btn anon-btn-ghost text-xs"
                    onClick={() =>
                      userAction(String(u.id), u.banned_at ? "restore" : "suspend")
                    }
                  >
                    {u.banned_at ? "Restore" : "Suspend"}
                  </button>
                </div>
              </div>
            ))
          )}
        </section>
      )}

      {tab === "moderation" && (
        <section className="space-y-3">
          <h2 className="font-semibold">🚨 Reports</h2>
          {reports.length === 0 ? (
            <p className="text-sm anon-muted">No reports yet.</p>
          ) : (
            reports.map((r) => (
              <div key={String(r.id)} className="anon-card p-4">
                <p className="font-medium">
                  {String(r.reason)} · {String(r.status)}
                </p>
                <p className="mt-1 text-xs anon-muted">
                  {String(r.target_type)}/{String(r.target_id)} ·{" "}
                  {new Date(String(r.created_at)).toLocaleString()}
                </p>
                {r.status === "open" || r.status === "reviewing" ? (
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      className="anon-btn anon-btn-primary text-xs"
                      onClick={() => reportAction(String(r.id), "resolve")}
                    >
                      Resolve
                    </button>
                    <button
                      type="button"
                      className="anon-btn anon-btn-ghost text-xs"
                      onClick={() => reportAction(String(r.id), "dismiss")}
                    >
                      Dismiss
                    </button>
                  </div>
                ) : null}
              </div>
            ))
          )}
        </section>
      )}

      {tab === "revenue" && kpis && (
        <section className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ["Gross paid", formatMoney(kpis.revenueTotalCents || 0)],
              ["Refunds", formatMoney(kpis.refundsCents || 0)],
              ["Net", formatMoney((kpis.revenueTotalCents || 0) - (kpis.refundsCents || 0))],
              ["Paid orders", kpis.paidOrders],
            ].map(([l, v]) => (
              <div key={String(l)} className="anon-card p-4">
                <div className="text-xs anon-muted">{l}</div>
                <div className="mt-2 text-lg font-semibold">{v}</div>
              </div>
            ))}
          </div>
          <p className="text-xs anon-muted">Wallet / Telegram Stars: Not supported</p>
          {tx.length === 0 ? (
            <p className="text-sm anon-muted">No transactions yet.</p>
          ) : (
            <div className="space-y-2">
              {tx.map((o) => (
                <div key={String(o.id)} className="anon-card flex justify-between gap-3 p-3 text-sm">
                  <div>
                    <p className="font-medium">
                      {String(o.gift_type)} · {formatMoney(Number(o.amount_cents) || 0)}
                    </p>
                    <p className="text-xs anon-muted">
                      {String(o.user_email || "—")} · {String(o.status)} · {String(o.provider)}
                    </p>
                  </div>
                  <span className="text-xs anon-muted">
                    {new Date(String(o.created_at)).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "products" && (
        <section className="space-y-2">
          {products.map((p) => (
            <div key={String(p.sku)} className="anon-card flex items-center justify-between gap-3 p-3">
              <div>
                <p className="font-medium">
                  {String(p.emoji)} {String(p.sku)}
                </p>
                <p className="text-xs anon-muted">
                  {formatMoney(Number(p.amountCents) || 0)} · {p.active ? "active" : "inactive"}
                </p>
              </div>
              <button
                type="button"
                className="anon-btn anon-btn-ghost text-xs"
                onClick={() => toggleProduct(String(p.sku), Boolean(p.active))}
              >
                {p.active ? "Disable" : "Enable"}
              </button>
            </div>
          ))}
        </section>
      )}

      {tab === "flags" && (
        <section className="space-y-2">
          {flags.map((f) => (
            <div key={String(f.key)} className="anon-card flex items-center justify-between gap-3 p-3">
              <div>
                <p className="font-mono text-sm">{String(f.key)}</p>
                <p className="text-xs anon-muted">rollout {String(f.rollout)}%</p>
              </div>
              <button
                type="button"
                className={`anon-btn text-xs ${f.enabled ? "anon-btn-primary" : "anon-btn-ghost"}`}
                onClick={() => toggleFlag(String(f.key), Boolean(f.enabled))}
              >
                {f.enabled ? "ON" : "OFF"}
              </button>
            </div>
          ))}
        </section>
      )}

      {tab === "health" && health && (
        <section className="space-y-3">
          <div className="anon-card p-5">
            <p className="text-sm anon-muted">Overall</p>
            <p className="mt-1 text-2xl font-semibold capitalize">{health.overall}</p>
            <p className="mt-2 text-xs anon-muted">{health.note}</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(health.checks).map(([k, v]) => (
              <div key={k} className="anon-card p-3 text-sm">
                <span className="anon-muted">{k}</span>
                <span className="ml-2 font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "audit" && (
        <section className="space-y-2">
          {audit.length === 0 ? (
            <p className="text-sm anon-muted">No admin actions yet.</p>
          ) : (
            audit.map((a) => (
              <div key={String(a.id)} className="anon-card p-3 text-sm">
                <p>
                  {String(a.admin_email || "admin")} · <strong>{String(a.action)}</strong>
                </p>
                <p className="text-xs anon-muted">
                  {String(a.target_type || "")} {String(a.target_id || "")} ·{" "}
                  {new Date(String(a.created_at)).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </section>
      )}
    </main>
  );
}
