"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { formatEur } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Package = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
};

type SalesOrder = {
  order_id: string;
  status: string;
  status_label: string;
  business_name: string;
  city: string;
  phone: string;
  whatsapp: string;
  package_name: string;
  price_eur: number;
  created_at: string;
  product_id: string | null;
  proposal_text: string;
  paid?: boolean;
  paid_at?: string | null;
};

export function SalesOrdersPanel() {
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/sales/orders`);
      if (res.ok) {
        const body = await res.json();
        setOrders(body.orders ?? []);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  const pending = useMemo(
    () =>
      orders.filter(
        (o) =>
          o.status === "pending_confirmation" ||
          o.status === "confirmed" ||
          o.status === "awaiting_payment"
      ),
    [orders]
  );

  async function confirm(orderId: string) {
    setBusyId(orderId);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/confirm`, { method: "POST" });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail) || "Ошибка");
      } else {
        setMessage(body.message);
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
      const res = await fetch(`${API}/api/sales/orders/${orderId}/start-production`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail) || "Ошибка");
      } else {
        setMessage(body.message);
        await load();
      }
    } finally {
      setBusyId(null);
    }
  }

  async function copyProposal(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setMessage("КП скопировано в буфер обмена");
    } catch {
      setMessage("Не удалось скопировать");
    }
  }

  if (loading) return null;
  if (!pending.length && !orders.some((o) => o.status === "in_production")) return null;

  return (
    <section className="genesis-card animate-fade-up border-emerald-500/25 bg-gradient-to-br from-emerald-950/20 to-genesis-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="genesis-label text-emerald-300/90">Заявки на сайт</p>
          <p className="mt-1 text-sm text-genesis-muted">
            Новая заявка → подтверждение → КП → производство
          </p>
        </div>
        <a
          href="/order"
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-emerald-500/30 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30"
        >
          Открыть страницу заказа ↗
        </a>
      </div>

      <ul className="mt-4 space-y-3">
        {orders.slice(0, 8).map((o) => (
          <li
            key={o.order_id}
            className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium">{o.business_name}</p>
                <p className="text-xs text-genesis-muted">
                  {o.city || "Город не указан"} · {o.package_name} · {formatEur(o.price_eur)}
                </p>
                <p className="mt-1 text-xs text-emerald-300/80">
                  {o.paid ? "🟢 Оплачено" : o.status_label}
                </p>
              </div>
              <span className="text-[10px] text-genesis-muted">
                {new Date(o.created_at).toLocaleString("ru-RU")}
              </span>
            </div>

            {(o.phone || o.whatsapp) && (
              <p className="mt-2 text-xs text-genesis-muted">
                {o.phone && `Тел: ${o.phone}`}
                {o.phone && o.whatsapp && " · "}
                {o.whatsapp && `WhatsApp: ${o.whatsapp}`}
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              {o.status === "pending_confirmation" && (
                <button
                  type="button"
                  disabled={busyId === o.order_id}
                  onClick={() => confirm(o.order_id)}
                  className="rounded-lg bg-emerald-600/80 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
                >
                  Подтвердить
                </button>
              )}
              {(o.status === "pending_confirmation" || o.status === "confirmed") && (
                <>
                  <button
                    type="button"
                    onClick={() => copyProposal(o.proposal_text)}
                    className="rounded-lg border border-genesis-border-subtle px-3 py-1.5 text-xs hover:bg-genesis-elevated"
                  >
                    Отправить КП
                  </button>
                  <button
                    type="button"
                    disabled={busyId === o.order_id}
                    onClick={() => startProduction(o.order_id)}
                    className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/30 disabled:opacity-50"
                  >
                    Запустить производство
                  </button>
                </>
              )}
              {o.status === "in_production" && o.product_id && (
                <a
                  href={`/products/${o.product_id}`}
                  className="rounded-lg border border-genesis-border-subtle px-3 py-1.5 text-xs hover:bg-genesis-elevated"
                >
                  Открыть продукт →
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>

      {message && <p className="mt-3 text-xs text-amber-200/90">{message}</p>}
    </section>
  );
}
