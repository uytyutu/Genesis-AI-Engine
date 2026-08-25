"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getBackendApiBase } from "../lib/backendApiBase";

const API = getBackendApiBase();

type UserRow = {
  customer_id: string;
  business_id?: string;
  name?: string;
  email?: string;
  phone?: string | null;
  company?: string | null;
  registered_at?: string;
  last_activity_at?: string;
  account_status?: string;
  products_count?: number;
  orders_count?: number;
  last_order_id?: string | null;
  last_order_status?: string | null;
  last_package?: string | null;
  is_demo_test?: boolean;
  layer?: string;
};

type UserCard = {
  business_id?: string;
  customer_id?: string;
  is_demo_test?: boolean;
  profile?: Record<string, string | null | undefined>;
  business_profile?: {
    ok?: boolean;
    has_profile?: boolean;
    note?: string | null;
    profile?: {
      company_name?: string;
      niche?: string;
      description?: string;
      language?: string;
      market?: string;
      contacts?: {
        phone?: string;
        email?: string;
        whatsapp?: string;
        website?: string;
      };
      address?: {
        street?: string;
        city?: string;
        postal_code?: string;
        country?: string;
      };
      services?: { name?: string; price_hint?: string }[];
      source?: string;
      updated_at?: string;
    } | null;
  };
  products?: {
    label?: string;
    status?: string;
    package?: string;
    order_id?: string;
  }[];
  websites?: {
    order_id?: string;
    package?: string;
    status?: string;
    download_ready?: boolean;
    order_href?: string | null;
    preview_href?: string | null;
    download_href?: string | null;
  }[];
  orders?: {
    order_id?: string;
    status?: string;
    package_name?: string;
    price_eur?: number;
    amount_eur?: number;
    payment_mode?: string;
  }[];
  finance?: {
    payments?: {
      order_id?: string;
      status?: string;
      package?: string;
      amount?: number;
      paid_at?: string;
      href?: string | null;
    }[];
    note?: string;
  };
  support?: {
    notes?: { note_id?: string; at?: string; author?: string; text?: string }[];
    tickets?: { ticket_id?: string; subject?: string; status?: string; created_at?: string }[];
  };
  timeline?: { at?: string; kind?: string; summary?: string }[];
  actions?: { id?: string; label?: string; href?: string | null; external?: boolean }[];
  chain?: {
    user?: string;
    orders?: string[];
    products?: string[];
    websites?: string[];
  };
};

function fmtDate(raw?: string | null) {
  if (!raw) return "—";
  try {
    return new Date(raw).toLocaleString("ru-RU");
  } catch {
    return String(raw).slice(0, 19);
  }
}

/** Sync deep-link without App Router remount (router.replace + useSearchParams = reload loop). */
function syncUsersUrl(customerId: string, query: string) {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams();
  if (customerId) params.set("id", customerId);
  const q = query.trim();
  if (q) params.set("q", q);
  const qs = params.toString();
  const next = qs ? `/users?${qs}` : "/users";
  const cur = `${window.location.pathname}${window.location.search}`;
  if (cur === next) return;
  window.history.replaceState(window.history.state, "", next);
}

function OwnerUsersDesk() {
  const searchParams = useSearchParams();
  const [q, setQ] = useState("");
  const [users, setUsers] = useState<UserRow[]>([]);
  const [emptyMsg, setEmptyMsg] = useState("Noch keine Kunden registriert.");
  const [card, setCard] = useState<UserCard | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hideDemo, setHideDemo] = useState(false);

  const openCard = useCallback(async (customerId: string, queryForUrl?: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/owner/users/${encodeURIComponent(customerId)}`,
        { cache: "no-store" },
      );
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || "Card failed");
      setCard(body as UserCard);
      syncUsersUrl(customerId, queryForUrl ?? q);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Card failed");
    } finally {
      setBusy(false);
    }
  }, [q]);

  const loadList = useCallback(
    async (query?: string) => {
      const term = (query ?? q).trim();
      setBusy(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (term) params.set("q", term);
        params.set("limit", "80");
        params.set("include_demo_test", hideDemo ? "false" : "true");
        const res = await fetch(`${API}/api/owner/users?${params}`, { cache: "no-store" });
        const body = await res.json().catch(() => null);
        if (!res.ok) throw new Error(body?.detail || "List failed");
        const rows: UserRow[] = Array.isArray(body?.users) ? body.users : [];
        setUsers(rows);
        setEmptyMsg(
          String(body?.empty_message_de || (term ? "Kein Kunde gefunden." : "Noch keine Kunden registriert.")),
        );
        // Do not auto-openCard here — that + URL sync remounted the page in a loop.
        if (term) syncUsersUrl("", term);
      } catch (e) {
        setError(e instanceof Error ? e.message : "List failed");
      } finally {
        setBusy(false);
      }
    },
    [q, hideDemo],
  );

  useEffect(() => {
    const initialQ = (searchParams.get("q") || "").trim();
    const initialId = (searchParams.get("id") || "").trim();
    if (initialQ) setQ(initialQ);
    let cancelled = false;
    void (async () => {
      setBusy(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (initialQ) params.set("q", initialQ);
        params.set("limit", "80");
        params.set("include_demo_test", "true");
        const res = await fetch(`${API}/api/owner/users?${params}`, { cache: "no-store" });
        const body = await res.json().catch(() => null);
        if (!res.ok) throw new Error(body?.detail || "List failed");
        if (cancelled) return;
        const rows: UserRow[] = Array.isArray(body?.users) ? body.users : [];
        setUsers(rows);
        setEmptyMsg(
          String(
            body?.empty_message_de ||
              (initialQ ? "Kein Kunde gefunden." : "Noch keine Kunden registriert."),
          ),
        );
        if (initialId) {
          const cres = await fetch(
            `${API}/api/owner/users/${encodeURIComponent(initialId)}`,
            { cache: "no-store" },
          );
          const cbody = await cres.json().catch(() => null);
          if (cres.ok && !cancelled) setCard(cbody as UserCard);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "List failed");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // Deep-link / first paint only — never depend on searchParams object (remount loop).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addNote = useCallback(async () => {
    if (!card?.customer_id || !note.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${API}/api/owner/clients/${encodeURIComponent(card.customer_id)}/notes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: note.trim(), author: "owner" }),
        },
      );
      if (!res.ok) throw new Error("note_failed");
      setNote("");
      await openCard(card.customer_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "note_failed");
    } finally {
      setBusy(false);
    }
  }, [card, note, openCard]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header>
        <p className="text-xs uppercase tracking-wide text-zinc-500">
          Mission Control · Компания · Пользователи
        </p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Owner Users</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Зарегистрированные клиенты Virtus Core · User → Orders → Products → Website / Support.
          Не параллельная БД — customer identity SSOT.
        </p>
      </header>

      <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void loadList(q);
          }}
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="customer_id · email · имя · company · телефон · Business ID"
            className="min-w-[240px] flex-1 rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "…" : "Найти"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setQ("");
              void loadList("");
            }}
            className="rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
          >
            Все
          </button>
        </form>
        <label className="mt-3 flex items-center gap-2 text-xs text-zinc-400">
          <input
            type="checkbox"
            checked={hideDemo}
            onChange={(e) => setHideDemo(e.target.checked)}
          />
          Скрыть demo/test пользователей
        </label>
        {error ? <p className="mt-2 text-sm text-amber-200">{error}</p> : null}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="mb-3 flex items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">Список</h2>
            <span className="text-xs text-zinc-500">{users.length} users</span>
          </div>
          {users.length === 0 ? (
            <p className="text-sm text-zinc-400">{emptyMsg}</p>
          ) : (
            <ul className="max-h-[70vh] space-y-2 overflow-y-auto">
              {users.map((u) => (
                <li key={u.customer_id}>
                  <button
                    type="button"
                    onClick={() => void openCard(u.customer_id)}
                    className={`w-full rounded-xl border px-3 py-3 text-left transition hover:bg-white/5 ${
                      card?.customer_id === u.customer_id
                        ? "border-emerald-500/40 bg-emerald-950/20"
                        : "border-white/10"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-white">
                        {u.name || u.company || u.email || u.customer_id}
                      </span>
                      {u.is_demo_test ? (
                        <span className="rounded border border-amber-500/40 px-1.5 py-0.5 text-[10px] uppercase text-amber-200">
                          demo/test
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-1 truncate text-xs text-zinc-400">
                      {u.email} · {u.company || "—"}
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-zinc-500">
                      {u.customer_id}
                      {u.business_id ? ` · ${u.business_id}` : ""}
                    </p>
                    <p className="mt-1 text-[11px] text-zinc-500">
                      {u.account_status || "active"} · products {u.products_count ?? 0} · orders{" "}
                      {u.orders_count ?? 0}
                      {u.last_order_id ? ` · last ${u.last_order_id}` : ""}
                    </p>
                    <p className="text-[10px] text-zinc-600">
                      reg {fmtDate(u.registered_at)} · activity {fmtDate(u.last_activity_at)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">Карточка пользователя</h2>
            {card ? (
              <button
                type="button"
                onClick={() => {
                  setCard(null);
                  syncUsersUrl("", q);
                }}
                className="rounded-lg border border-white/15 px-2.5 py-1 text-xs text-zinc-300 hover:bg-white/5"
              >
                Закрыть
              </button>
            ) : null}
          </div>
          {!card ? (
            <p className="text-sm text-zinc-400">Выберите пользователя слева.</p>
          ) : (
            <div className="space-y-4 text-sm">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-lg font-semibold text-white">
                    {card.profile?.name || card.profile?.company || card.customer_id}
                  </h3>
                  {card.is_demo_test ? (
                    <span className="rounded border border-amber-500/40 px-1.5 py-0.5 text-[10px] uppercase text-amber-200">
                      demo/test
                    </span>
                  ) : null}
                </div>
                <p className="mt-1 text-zinc-400">{card.profile?.email}</p>
                <p className="font-mono text-[11px] text-zinc-500">
                  {card.customer_id}
                  {card.business_id ? ` · ${card.business_id}` : ""}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {card.profile?.company || "—"} · {card.profile?.phone || "без телефона"} ·{" "}
                  {card.profile?.account_status || "active"}
                </p>
                <p className="text-[11px] text-zinc-600">
                  Registered {fmtDate(card.profile?.registered_at)} · Last activity{" "}
                  {fmtDate(card.profile?.last_activity_at)}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-zinc-400">
                Цепочка: User → Business Profile → Orders ({card.chain?.orders?.length ?? 0}) →
                Products ({card.chain?.products?.length ?? 0}) → Websites (
                {card.chain?.websites?.length ?? 0})
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">
                  Business Profile SSOT
                </h4>
                {!card.business_profile?.has_profile || !card.business_profile.profile ? (
                  <p className="mt-1 text-sm text-amber-200/90">
                    {card.business_profile?.note ||
                      "Профиль ещё не заполнен — Giveaway/Order не создают вторую сущность."}
                  </p>
                ) : (
                  <div className="mt-2 space-y-2 rounded-xl border border-emerald-500/20 bg-emerald-950/15 px-3 py-3 text-sm text-zinc-300">
                    <p className="font-medium text-white">
                      {card.business_profile.profile.company_name || "—"}
                      {card.business_profile.profile.niche
                        ? ` · ${card.business_profile.profile.niche}`
                        : ""}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {card.business_profile.profile.market || "—"} /{" "}
                      {card.business_profile.profile.language || "—"}
                      {card.business_profile.profile.source
                        ? ` · source ${card.business_profile.profile.source}`
                        : ""}
                    </p>
                    {card.business_profile.profile.description ? (
                      <p className="text-xs leading-relaxed text-zinc-400">
                        {card.business_profile.profile.description.slice(0, 280)}
                        {card.business_profile.profile.description.length > 280 ? "…" : ""}
                      </p>
                    ) : null}
                    <p className="text-xs text-zinc-400">
                      {[
                        card.business_profile.profile.contacts?.phone,
                        card.business_profile.profile.contacts?.whatsapp
                          ? `WA ${card.business_profile.profile.contacts.whatsapp}`
                          : null,
                        card.business_profile.profile.contacts?.email,
                        [
                          card.business_profile.profile.address?.postal_code,
                          card.business_profile.profile.address?.city,
                        ]
                          .filter(Boolean)
                          .join(" "),
                      ]
                        .filter(Boolean)
                        .join(" · ") || "Контакты не заполнены"}
                    </p>
                    {(card.business_profile.profile.services || []).length > 0 ? (
                      <ul className="text-xs text-zinc-400">
                        {(card.business_profile.profile.services || []).slice(0, 6).map((s, i) => (
                          <li key={`${s.name}-${i}`}>
                            {s.name}
                            {s.price_hint ? ` · ${s.price_hint}` : ""}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <Link
                  href="/orders"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs text-sky-200 hover:bg-white/5"
                >
                  Заказы
                </Link>
                <Link
                  href="/factory"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs text-sky-200 hover:bg-white/5"
                >
                  Продукты
                </Link>
                <Link
                  href="/support"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs text-sky-200 hover:bg-white/5"
                >
                  Поддержка
                </Link>
                {(card.actions || [])
                  .filter((a) => a.href && (a.id?.startsWith("preview") || a.id?.startsWith("zip")))
                  .slice(0, 6)
                  .map((a) => (
                    <a
                      key={a.id}
                      href={
                        a.href?.startsWith("/api/")
                          ? `${API}${a.href}`
                          : a.href || "#"
                      }
                      target={a.external ? "_blank" : undefined}
                      rel={a.external ? "noopener noreferrer" : undefined}
                      className="rounded-lg border border-emerald-500/30 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30"
                    >
                      {a.label}
                    </a>
                  ))}
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">Products</h4>
                {(card.products || []).length === 0 ? (
                  <p className="mt-1 text-zinc-500">Нет продуктов</p>
                ) : (
                  <ul className="mt-1 space-y-1">
                    {(card.products || []).map((p) => (
                      <li key={`${p.order_id}-${p.label}`} className="text-zinc-300">
                        {p.label} · {p.package} · {p.status}
                        {p.order_id ? (
                          <>
                            {" "}
                            <Link
                              href={`/orders#${p.order_id}`}
                              className="text-sky-300 hover:underline"
                            >
                              {p.order_id}
                            </Link>
                          </>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">Websites</h4>
                {(card.websites || []).length === 0 ? (
                  <p className="mt-1 text-zinc-500">Нет website-продуктов</p>
                ) : (
                  <ul className="mt-1 space-y-2">
                    {(card.websites || []).map((w) => (
                      <li key={w.order_id} className="rounded-lg border border-white/10 px-2 py-2">
                        <p className="text-zinc-200">
                          {w.package} · {w.status}
                        </p>
                        <div className="mt-1 flex flex-wrap gap-2 text-xs">
                          {w.order_href ? (
                            <Link href={w.order_href} className="text-sky-300 hover:underline">
                              Order
                            </Link>
                          ) : null}
                          {w.preview_href ? (
                            <a
                              href={`${API}${w.preview_href}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-emerald-300 hover:underline"
                            >
                              Preview
                            </a>
                          ) : null}
                          {w.download_href ? (
                            <a
                              href={`${API}${w.download_href}`}
                              className="text-emerald-300 hover:underline"
                            >
                              ZIP
                            </a>
                          ) : (
                            <span className="text-zinc-600">ZIP не ready</span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">Payments</h4>
                <p className="mt-1 text-[11px] text-zinc-500">{card.finance?.note}</p>
                <ul className="mt-1 space-y-1">
                  {(card.finance?.payments || []).slice(0, 12).map((p) => (
                    <li key={p.order_id} className="text-zinc-300">
                      {p.order_id} · {p.status} · {p.package} · {p.amount ?? "—"} €
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">Support notes</h4>
                <ul className="mt-1 max-h-32 space-y-1 overflow-y-auto text-xs text-zinc-400">
                  {(card.support?.notes || []).length === 0 ? (
                    <li>Нет заметок</li>
                  ) : (
                    (card.support?.notes || []).slice(-8).reverse().map((n) => (
                      <li key={n.note_id}>
                        {fmtDate(n.at)} · {n.author}: {n.text}
                      </li>
                    ))
                  )}
                </ul>
                <div className="mt-2 flex gap-2">
                  <input
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Owner note…"
                    className="flex-1 rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
                  />
                  <button
                    type="button"
                    disabled={busy || !note.trim()}
                    onClick={() => void addNote()}
                    className="rounded-lg bg-emerald-700 px-3 py-1.5 text-xs text-white disabled:opacity-40"
                  >
                    Добавить
                  </button>
                </div>
              </div>

              <div>
                <h4 className="text-xs uppercase tracking-wide text-zinc-500">Timeline</h4>
                <ul className="mt-1 max-h-40 space-y-1 overflow-y-auto text-xs text-zinc-500">
                  {(card.timeline || []).slice(0, 12).map((t, i) => (
                    <li key={`${t.at}-${i}`}>
                      {fmtDate(t.at)} · {t.kind}: {t.summary}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default function OwnerUsersPage() {
  return (
    <Suspense fallback={<main className="p-8 text-sm text-zinc-400">Laden…</main>}>
      <OwnerUsersDesk />
    </Suspense>
  );
}
