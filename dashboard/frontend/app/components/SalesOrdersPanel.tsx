"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDeferredMount } from "../lib/useDeferredMount";
import { formatEur } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";
import { fetchApi } from "../lib/fetchApi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SalesOrder = {
  order_id: string;
  status: string;
  status_label: string;
  business_name: string;
  city: string;
  phone: string;
  whatsapp: string;
  email?: string;
  customer_id?: string | null;
  package_name: string;
  package_id?: string | null;
  product_kind?: string | null;
  price_eur: number;
  created_at: string;
  product_id: string | null;
  proposal_text: string;
  paid?: boolean;
  paid_at?: string | null;
  download_ready?: boolean;
};

type Props = {
  /** Compact widget vs full Orders desk */
  mode?: "widget" | "desk";
};

export function SalesOrdersPanel({ mode = "desk" }: Props) {
  const deferred = useDeferredMount(mode === "desk" ? 0 : 1800);
  const ready = mode === "desk" ? true : deferred;
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "ready">("all");

  const load = useCallback(async () => {
    try {
      const res = await fetchApi(`${API}/api/sales/orders`, { timeoutMs: 10_000 });
      if (res.ok) {
        const body = await res.json();
        setOrders(body.orders ?? []);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!ready) return;
    void load();
    const t = setInterval(() => void load(), 20000);
    return () => clearInterval(t);
  }, [ready, load]);

  const visible = useMemo(() => {
    if (filter === "ready") {
      return orders.filter(
        (o) => o.download_ready || o.status === "ready" || o.status === "delivered",
      );
    }
    if (filter === "active") {
      return orders.filter((o) =>
        [
          "pending_confirmation",
          "confirmed",
          "awaiting_payment",
          "paid",
          "in_production",
        ].includes(o.status),
      );
    }
    return orders;
  }, [orders, filter]);

  if (!ready) return null;

  async function confirm(orderId: string) {
    setBusyId(orderId);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/confirm`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail) || "Ошибка подтверждения");
      } else {
        setMessage(body.message || "Подтверждено");
        await load();
      }
    } finally {
      setBusyId(null);
    }
  }

  async function startProduction(orderId: string) {
    setBusyId(orderId);
    setMessage("");
    try {
      const res = await fetch(
        `${API}/api/sales/orders/${orderId}/start-production`,
        { method: "POST" },
      );
      const body = await res.json();
      if (!res.ok) {
        setMessage(
          formatApiDetail(body.detail) || "Производство не запущено",
        );
      } else {
        setMessage(body.message || "Производство запущено");
        await load();
      }
    } finally {
      setBusyId(null);
    }
  }

  async function copyProposal(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setMessage("КП скопировано (отправка email — вручную)");
    } catch {
      setMessage("Не удалось скопировать");
    }
  }

  async function markDelivered(productId: string) {
    setMessage("");
    try {
      const res = await fetch(
        `${API}/api/factory/products/${encodeURIComponent(productId)}/delivered`,
        { method: "POST" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(String(body?.detail || "Выдача не отмечена"));
        return;
      }
      setMessage("Выдача клиенту отмечена");
      await load();
    } catch {
      setMessage("Ошибка сети");
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-zinc-500">
        {mode === "desk" ? "Загрузка заказов…" : null}
      </p>
    );
  }

  if (mode === "widget" && !orders.length) {
    return null;
  }

  return (
    <section
      className={
        mode === "desk"
          ? "space-y-4"
          : "genesis-card animate-fade-up border-emerald-500/25 bg-gradient-to-br from-emerald-950/20 to-genesis-panel p-5"
      }
    >
      {mode === "desk" ? (
        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              ["all", "Все"],
              ["active", "В работе"],
              ["ready", "Готово / ZIP"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setFilter(id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                filter === id
                  ? "bg-emerald-500/20 text-emerald-100"
                  : "border border-white/10 text-zinc-400 hover:bg-white/5"
              }`}
            >
              {label}
            </button>
          ))}
          <span className="ml-auto text-[11px] text-zinc-500">
            {orders.length} заказов
          </span>
        </div>
      ) : (
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="genesis-label text-emerald-300/90">Заказы</p>
            <p className="mt-1 text-sm text-genesis-muted">
              Подтверждение → производство → Preview / ZIP
            </p>
          </div>
          <Link
            href="/orders"
            className="rounded-lg border border-emerald-500/30 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30"
          >
            Открыть Orders →
          </Link>
        </div>
      )}

      {!visible.length ? (
        <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-zinc-400">
          Нет заказов в этом фильтре.
        </div>
      ) : (
        <ul className="space-y-3">
          {(mode === "widget" ? visible.slice(0, 8) : visible).map((o) => (
            <li
              key={o.order_id}
              id={o.order_id}
              className="rounded-xl border border-white/10 bg-black/25 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-white">{o.business_name}</p>
                  <p className="text-xs text-zinc-400">
                    {o.city || "—"} · {o.package_name} · {formatEur(o.price_eur)}
                  </p>
                  <p className="mt-1 text-xs text-emerald-300/80">
                    {o.paid ? "🟢 Оплачено / в работе" : o.status_label}
                    {o.download_ready ? " · ZIP готов" : ""}
                  </p>
                  <p className="mt-1 text-[11px] text-zinc-500">
                    {o.order_id}
                    {o.email ? ` · ${o.email}` : ""}
                    {o.customer_id ? ` · ${o.customer_id}` : ""}
                  </p>
                </div>
                <span className="text-[10px] text-zinc-500">
                  {new Date(o.created_at).toLocaleString("ru-RU")}
                </span>
              </div>

              {(o.phone || o.whatsapp) && (
                <p className="mt-2 text-xs text-zinc-500">
                  {o.phone && `Тел: ${o.phone}`}
                  {o.phone && o.whatsapp && " · "}
                  {o.whatsapp && `WhatsApp: ${o.whatsapp}`}
                </p>
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                {o.customer_id ? (
                  <Link
                    href={`/clients?q=${encodeURIComponent(o.customer_id)}`}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                  >
                    Customer →
                  </Link>
                ) : o.email ? (
                  <Link
                    href={`/clients?q=${encodeURIComponent(o.email)}`}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                  >
                    Найти клиента →
                  </Link>
                ) : null}

                {o.status === "pending_confirmation" && (
                  <button
                    type="button"
                    disabled={busyId === o.order_id}
                    onClick={() => void confirm(o.order_id)}
                    className="rounded-lg bg-emerald-600/80 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
                  >
                    Подтвердить
                  </button>
                )}

                {(o.status === "pending_confirmation" ||
                  o.status === "confirmed" ||
                  o.status === "paid") && (
                  <>
                    {o.proposal_text ? (
                      <button
                        type="button"
                        onClick={() => void copyProposal(o.proposal_text)}
                        className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                      >
                        Копировать КП
                      </button>
                    ) : null}
                    <button
                      type="button"
                      disabled={busyId === o.order_id}
                      onClick={() => void startProduction(o.order_id)}
                      className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30 disabled:opacity-50"
                    >
                      Start production
                    </button>
                  </>
                )}

                {o.product_id ? (
                  <>
                    <Link
                      href={`/products/${o.product_id}`}
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                    >
                      Factory →
                    </Link>
                    <a
                      href={`${API}/api/factory/products/${o.product_id}/preview`}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                    >
                      Preview ↗
                    </a>
                  </>
                ) : null}

                {o.download_ready ? (
                  <a
                    href={`${API}/api/sales/orders/${o.order_id}/download`}
                    className="rounded-lg border border-sky-500/40 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-950/20"
                  >
                    ZIP ↓
                  </a>
                ) : null}

                {o.product_id && o.status !== "delivered" ? (
                  <button
                    type="button"
                    onClick={() => void markDelivered(o.product_id!)}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                  >
                    Отметить выдачу
                  </button>
                ) : null}

                <Link
                  href={`/order/status/${o.order_id}`}
                  className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-400 hover:bg-white/5"
                >
                  Client status ↗
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}

      {message ? <p className="mt-3 text-xs text-amber-200/90">{message}</p> : null}
    </section>
  );
}
