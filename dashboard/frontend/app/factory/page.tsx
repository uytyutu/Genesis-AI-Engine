"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { formatEur } from "../lib/formatEur";
import { fetchApi } from "../lib/fetchApi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SalesOrder = {
  order_id: string;
  status: string;
  status_label: string;
  business_name: string;
  city: string;
  package_name: string;
  package_id?: string | null;
  product_kind?: string | null;
  price_eur: number;
  created_at: string;
  product_id: string | null;
  paid?: boolean;
  download_ready?: boolean;
  email?: string;
  customer_id?: string | null;
};

function kindLabel(o: SalesOrder): string {
  const pk = String(o.product_kind || o.package_id || "").toLowerCase();
  if (pk.includes("shop") || pk.includes("ecommerce") || pk.includes("store")) {
    return "Shop";
  }
  if (pk.includes("bot") || pk.includes("ai_") || pk.includes("chatbot")) {
    return "AI Assistant";
  }
  if (pk.includes("repair")) return "Website Repair";
  return "Website";
}

/** MC 2.0 — Products / Factory delivery desk. */
export default function FactoryProductsPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await fetchApi(`${API}/api/sales/orders`, {
        timeoutMs: 10_000,
      });
      if (res.ok) {
        const body = await res.json();
        setOrders(body.orders ?? []);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const inFlight = useMemo(
    () =>
      orders.filter((o) =>
        ["paid", "in_production", "ready", "delivered", "confirmed"].includes(
          o.status,
        ),
      ),
    [orders],
  );

  const markDelivered = async (productId: string) => {
    setMessage("");
    try {
      const res = await fetch(
        `${API}/api/factory/products/${encodeURIComponent(productId)}/delivered`,
        { method: "POST" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(String(body?.detail || "Не удалось отметить выдачу"));
        return;
      }
      setMessage("Отмечено: выдано клиенту");
      await load();
    } catch {
      setMessage("Ошибка сети");
    }
  };

  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-8 text-zinc-100">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-zinc-500">
            Mission Control · Продукты
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-white">
            Продукты · Factory
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Website / Shop / AI — клиент, статус, Preview, ZIP, выдача.
          </p>
        </div>
        <Link
          href="/create"
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
        >
          Factory Wizard →
        </Link>
      </header>

      {loading ? (
        <p className="text-sm text-zinc-500">Загрузка…</p>
      ) : inFlight.length === 0 ? (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-8 text-center text-sm text-zinc-400">
          Нет продуктов в производстве. Новые заказы появятся в{" "}
          <Link href="/orders" className="text-emerald-300 hover:underline">
            Orders
          </Link>
          .
        </div>
      ) : (
        <ul className="space-y-3">
          {inFlight.map((o) => (
            <li
              key={o.order_id}
              className="rounded-xl border border-white/10 bg-black/25 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-emerald-300/80">
                    {kindLabel(o)}
                  </p>
                  <p className="mt-0.5 font-medium text-white">
                    {o.business_name}
                  </p>
                  <p className="text-xs text-zinc-400">
                    {o.package_name} · {formatEur(o.price_eur)} ·{" "}
                    {o.status_label}
                  </p>
                  <p className="mt-1 text-[11px] text-zinc-500">
                    Order {o.order_id}
                    {o.customer_id ? ` · Customer ${o.customer_id}` : ""}
                    {o.email ? ` · ${o.email}` : ""}
                  </p>
                </div>
                <span className="text-[10px] text-zinc-500">
                  {o.created_at
                    ? new Date(o.created_at).toLocaleString("ru-RU")
                    : ""}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {o.customer_id ? (
                  <Link
                    href={`/clients?q=${encodeURIComponent(o.customer_id)}`}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                  >
                    Customer →
                  </Link>
                ) : null}
                <Link
                  href={`/orders#${o.order_id}`}
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                >
                  Order →
                </Link>
                {o.product_id ? (
                  <>
                    <Link
                      href={`/products/${o.product_id}`}
                      className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30"
                    >
                      Factory product →
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
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
                  >
                    ZIP ↓
                  </a>
                ) : null}
                {o.product_id && o.status !== "delivered" ? (
                  <button
                    type="button"
                    onClick={() => void markDelivered(o.product_id!)}
                    className="rounded-lg border border-sky-500/40 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-950/30"
                  >
                    Отметить выдачу
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
      {message ? <p className="text-xs text-amber-200/90">{message}</p> : null}
    </main>
  );
}
