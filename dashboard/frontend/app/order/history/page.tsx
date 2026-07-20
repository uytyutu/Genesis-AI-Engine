"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../../components/PublicPageShell";
import { listStoredOrders, type StoredOrderRef } from "../../lib/orderHistory";

export default function OrderHistoryPage() {
  const { t } = useTranslation("site");
  const [orders, setOrders] = useState<StoredOrderRef[]>([]);

  useEffect(() => {
    setOrders(listStoredOrders());
  }, []);

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-8">
        <h1 className="text-2xl font-bold">{t("order.status.orderHistory")}</h1>
        <p className="mt-2 text-sm text-genesis-muted">{t("order.status.bookmark")}</p>

        {orders.length === 0 ? (
          <p className="mt-8 text-sm text-genesis-muted">{t("order.status.notFound")}</p>
        ) : (
          <ul className="mt-6 space-y-3">
            {orders.map((o) => (
              <li key={o.order_id}>
                <Link
                  href={`/order/status/${o.order_id}`}
                  className="block rounded-2xl border border-genesis-border-subtle bg-genesis-panel/60 px-4 py-4 hover:border-emerald-500/40"
                >
                  <p className="font-mono text-xs text-genesis-muted">№ {o.order_id}</p>
                  <p className="mt-1 font-medium">{o.business_name || "—"}</p>
                  <p className="text-xs text-genesis-muted">
                    {o.package_name || "—"}
                    {o.price_label ? ` · ${o.price_label}` : ""}
                    {o.status ? ` · ${o.status}` : ""}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <Link href="/order" className="mt-8 inline-block text-sm text-genesis-accent hover:underline">
          ← {t("order.status.newOrder")}
        </Link>
      </main>
    </PublicPageShell>
  );
}
