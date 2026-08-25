"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { BRAND_NAME } from "../lib/publicBrand";

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type LookupHit = {
  customer_id: string;
  business_id?: string;
  name?: string;
  email?: string;
  phone?: string | null;
  company?: string | null;
  country?: string;
  registered_at?: string;
  account_status?: string;
};

type ClientCard = {
  business_id?: string;
  customer_id?: string;
  profile?: Record<string, string | null | undefined>;
  products?: { label?: string; status?: string; package?: string; order_id?: string }[];
  finance?: { payments?: { order_id?: string; status?: string; amount?: number; paid_at?: string }[] };
  commerce?: { stores?: { order_id?: string; stripe?: boolean | null; shipping?: boolean | null; smtp?: boolean | null }[] };
  domains?: { domain?: string; publish_status?: string; order_id?: string }[];
  support?: {
    notes?: { note_id?: string; at?: string; author?: string; text?: string }[];
    tickets?: { ticket_id?: string; subject?: string; status?: string; created_at?: string }[];
  };
  timeline?: { at?: string; kind?: string; summary?: string }[];
  vector?: { platform_visitor_id?: string; interests?: string[] };
};

export default function ClientsSupportPage() {
  const searchParams = useSearchParams();
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<LookupHit[]>([]);
  const [card, setCard] = useState<ClientCard | null>(null);
  const [note, setNote] = useState("");
  const [ticketSubject, setTicketSubject] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const openCard = useCallback(async (customerId: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/owner/clients/${encodeURIComponent(customerId)}`, {
        cache: "no-store",
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || "Card failed");
      setCard(body as ClientCard);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Card failed");
    } finally {
      setBusy(false);
    }
  }, []);

  const search = useCallback(
    async (query?: string) => {
      const term = (query ?? q).trim();
      if (!term) return;
      setBusy(true);
      setError(null);
      try {
        const res = await fetch(
          `${API}/api/owner/clients/lookup?q=${encodeURIComponent(term)}&limit=20`,
          { cache: "no-store" },
        );
        const body = await res.json().catch(() => null);
        if (!res.ok) throw new Error(body?.detail || "Lookup failed");
        const results: LookupHit[] = Array.isArray(body?.results)
          ? body.results
          : [];
        setHits(results);
        if (!results.length) {
          setCard(null);
          return;
        }
        if (results.length === 1) {
          await openCard(results[0].customer_id);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Lookup failed");
      } finally {
        setBusy(false);
      }
    },
    [q, openCard],
  );

  useEffect(() => {
    const initial = (searchParams.get("q") || "").trim();
    if (!initial) return;
    setQ(initial);
    void search(initial);
    // One-shot deep link from Orders / Products
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const copyId = async () => {
    if (!card?.business_id) return;
    try {
      await navigator.clipboard.writeText(card.business_id);
    } catch {
      /* ignore */
    }
  };

  const addNote = async () => {
    if (!card?.customer_id || !note.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${API}/api/owner/clients/${encodeURIComponent(card.customer_id)}/notes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: note.trim() }),
        },
      );
      if (!res.ok) throw new Error("Note failed");
      setNote("");
      await openCard(card.customer_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Note failed");
    } finally {
      setBusy(false);
    }
  };

  const createTicket = async () => {
    if (!card?.customer_id || !ticketSubject.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${API}/api/owner/clients/${encodeURIComponent(card.customer_id)}/tickets`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subject: ticketSubject.trim() }),
        },
      );
      if (!res.ok) throw new Error("Ticket failed");
      setTicketSubject("");
      await openCard(card.customer_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ticket failed");
    } finally {
      setBusy(false);
    }
  };

  const p = card?.profile || {};

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-emerald-500/25 bg-emerald-950/15 p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-400/80">
                {BRAND_NAME} · Support Center
              </p>
              <h1 className="mt-2 text-2xl font-semibold">Client Card</h1>
              <p className="mt-1 text-sm text-genesis-muted">
                Поиск по Business ID, email, компании, телефону. Не Gen2 CRM — инструмент
                сопровождения первых клиентов.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href="/support"
                className="rounded-lg border border-genesis-border px-3 py-1.5 text-sm hover:bg-genesis-elevated/40"
              >
                Inbox
              </Link>
              <Link
                href="/global-analytics"
                className="rounded-lg border border-genesis-border px-3 py-1.5 text-sm hover:bg-genesis-elevated/40"
              >
                Mission Control
              </Link>
            </div>
          </div>

          <form
            className="mt-5 flex flex-col gap-2 sm:flex-row"
            onSubmit={(e) => {
              e.preventDefault();
              void search();
            }}
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="VC-8Q4M-L72P · email · компания · телефон"
              className="min-h-[44px] flex-1 rounded-xl border border-white/15 bg-black/30 px-4 text-sm text-white"
            />
            <button
              type="submit"
              disabled={busy}
              className="min-h-[44px] rounded-xl bg-emerald-500 px-5 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
            >
              Найти
            </button>
          </form>
          {error ? (
            <p className="mt-3 text-sm text-rose-400" role="alert">
              {error}
            </p>
          ) : null}
        </header>

        {hits.length > 0 ? (
          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-white">Результаты</h2>
            <ul className="space-y-2">
              {hits.map((h) => (
                <li key={h.customer_id}>
                  <button
                    type="button"
                    onClick={() => void openCard(h.customer_id)}
                    className="flex w-full items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-left text-sm hover:border-emerald-500/40"
                  >
                    <span>
                      <span className="font-semibold text-emerald-200">
                        {h.business_id || "—"}
                      </span>
                      <span className="mt-0.5 block text-white">{h.name || h.email}</span>
                      <span className="text-xs text-genesis-muted">
                        {h.email}
                        {h.company ? ` · ${h.company}` : ""}
                      </span>
                    </span>
                    <span className="text-xs text-emerald-300">Открыть →</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {card ? (
          <section className="space-y-5 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-300/80">
                  Business ID
                </p>
                <p className="mt-1 font-mono text-xl font-semibold text-white">
                  {card.business_id || "—"}
                </p>
                <p className="mt-1 text-sm text-genesis-muted">
                  {p.name} · {p.email}
                  {p.company ? ` · ${p.company}` : ""}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void copyId()}
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-sm hover:bg-white/5"
                >
                  📋 Копировать ID
                </button>
                {p.email ? (
                  <a
                    href={`mailto:${p.email}`}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-sm hover:bg-white/5"
                  >
                    ✉️ Написать
                  </a>
                ) : null}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-white">Профиль</h3>
                <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                  <li>Страна: {p.country || "—"}</li>
                  <li>Язык: {p.locale || "—"}</li>
                  <li>Регистрация: {p.registered_at || "—"}</li>
                  <li>Статус: {p.account_status || "—"}</li>
                  <li>Телефон: {p.phone || "—"}</li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Продукты</h3>
                <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                  {(card.products || []).length === 0 ? (
                    <li className="text-genesis-muted">Пока нет заказов</li>
                  ) : (
                    (card.products || []).map((pr) => (
                      <li key={`${pr.order_id}-${pr.label}`}>
                        {pr.order_id ? (
                          <Link
                            href={`/orders#${pr.order_id}`}
                            className="text-emerald-300 hover:underline"
                          >
                            {pr.label} · {pr.status} · {pr.package}
                          </Link>
                        ) : (
                          <>
                            {pr.label} · {pr.status} · {pr.package}
                          </>
                        )}
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>

            {(card.commerce?.stores || []).length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold text-white">Commerce</h3>
                <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                  {(card.commerce?.stores || []).map((s) => (
                    <li key={s.order_id}>
                      {s.order_id}: Stripe {s.stripe ? "✓" : "—"} · Shipping{" "}
                      {s.shipping ? "✓" : "—"} · SMTP {s.smtp ? "✓" : "—"}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-white">Заметки поддержки</h3>
                <ul className="mt-2 max-h-40 space-y-2 overflow-y-auto text-sm text-zinc-300">
                  {(card.support?.notes || []).length === 0 ? (
                    <li className="text-genesis-muted">Пока нет</li>
                  ) : (
                    (card.support?.notes || [])
                      .slice()
                      .reverse()
                      .map((n) => (
                        <li key={n.note_id} className="border-b border-white/5 pb-2">
                          <span className="text-xs text-genesis-muted">{n.at}</span>
                          <p>{n.text}</p>
                        </li>
                      ))
                  )}
                </ul>
                <div className="mt-3 flex gap-2">
                  <input
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Внутренняя заметка…"
                    className="flex-1 rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => void addNote()}
                    className="rounded-lg bg-emerald-500/90 px-3 py-2 text-sm font-semibold text-black"
                  >
                    +
                  </button>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Тикеты</h3>
                <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-sm text-zinc-300">
                  {(card.support?.tickets || []).length === 0 ? (
                    <li className="text-genesis-muted">Пока нет</li>
                  ) : (
                    (card.support?.tickets || []).map((t) => (
                      <li key={t.ticket_id}>
                        {t.ticket_id} · {t.status} · {t.subject}
                      </li>
                    ))
                  )}
                </ul>
                <div className="mt-3 flex gap-2">
                  <input
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                    placeholder="Тема тикета…"
                    className="flex-1 rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => void createTicket()}
                    className="rounded-lg border border-white/15 px-3 py-2 text-sm"
                  >
                    Тикет
                  </button>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-white">Таймлайн</h3>
              <ol className="mt-2 max-h-56 space-y-2 overflow-y-auto text-sm text-zinc-300">
                {(card.timeline || []).length === 0 ? (
                  <li className="text-genesis-muted">Пока пусто</li>
                ) : (
                  (card.timeline || []).map((ev, i) => (
                    <li key={`${ev.at}-${i}`} className="border-b border-white/5 pb-2">
                      <span className="text-xs text-genesis-muted">{ev.at}</span>
                      <p>
                        <span className="text-emerald-200">{ev.kind}</span> — {ev.summary}
                      </p>
                    </li>
                  ))
                )}
              </ol>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
