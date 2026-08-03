"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type ClientOrder = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  package_id?: string;
  price_eur?: number;
  price_label?: string;
  status?: string;
  status_label?: string;
  download_ready?: boolean;
  download_url?: string | null;
  paid?: boolean;
};

export default function ClientOrdersPage() {
  const [orders, setOrders] = useState<ClientOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      setError("Войдите в кабинет, чтобы видеть заказы.");
      setOrders([]);
      return;
    }
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/orders`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || `HTTP ${res.status}`);
      }
      setOrders(Array.isArray(body.orders) ? body.orders : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить заказы");
      setOrders([]);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ClientWorkspaceShell
      title="Мои заказы"
      subtitle="Landing и услуги, привязанные к вашему аккаунту."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {orders === null ? (
        <p className="text-sm text-zinc-500">Загрузка…</p>
      ) : orders.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>Пока нет заказов в кабинете.</p>
          <p className="mt-2">
            Оформите Landing в магазине услуг — после оплаты заказ появится здесь, с ZIP.
          </p>
          <Link
            href="/client/shop"
            className="mt-4 inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
          >
            Открыть магазин →
          </Link>
        </div>
      ) : (
        <ul className="grid gap-3">
          {orders.map((o) => (
            <li
              key={o.order_id}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-semibold text-white">
                    {o.business_name || "Проект"}
                  </p>
                  <p className="mt-1 text-sm text-zinc-400">
                    {o.package_name || o.package_id} · {o.price_label || `${o.price_eur ?? ""} €`}
                  </p>
                  <p className="mt-2 text-xs uppercase tracking-wide text-emerald-300">
                    {o.status_label || o.status}
                  </p>
                  <p className="mt-1 font-mono text-[11px] text-zinc-500">{o.order_id}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link
                    href={`/order/status/${o.order_id}`}
                    className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                  >
                    Статус
                  </Link>
                  {o.download_ready && o.download_url ? (
                    <a
                      href={`${API}${o.download_url}`}
                      className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black hover:brightness-110"
                    >
                      Скачать ZIP
                    </a>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
