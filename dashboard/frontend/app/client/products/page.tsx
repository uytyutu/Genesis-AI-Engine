"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type MyProduct = {
  product_id: string;
  product_type: string;
  display_name: string;
  status: string;
  source: string;
};

type ClientOrder = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  status_label?: string;
  status?: string;
  download_ready?: boolean;
  download_url?: string | null;
  product_kind?: string;
  product_id?: string | null;
};

export default function ClientProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState<MyProduct[] | null>(null);
  const [orders, setOrders] = useState<ClientOrder[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const portalProducts = await portalFetch<MyProduct[]>("/portal/my-products").catch(
        (err) => {
          if (err instanceof PortalApiError && err.status === 401) {
            throw err;
          }
          return [] as MyProduct[];
        },
      );
      setProducts(portalProducts);

      if (getClientToken()) {
        const res = await fetch(`${API}/api/client/orders`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        const body = await res.json().catch(() => ({}));
        if (res.ok && Array.isArray(body.orders)) {
          setOrders(
            body.orders.filter(
              (o: ClientOrder) =>
                !o.product_kind || o.product_kind === "website" || !String(o.product_kind).startsWith("bot"),
            ),
          );
        }
      }
    } catch (err) {
      if (err instanceof PortalApiError && err.status === 401) {
        router.replace("/client/login");
        return;
      }
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
      else setError(formatApiDetail(err));
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const empty = (products === null || products.length === 0) && orders.length === 0;

  return (
    <ClientWorkspaceShell
      title="Мои продукты"
      subtitle="Сайты и услуги в вашем кабинете. ZIP — один из способов получить результат."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {products === null ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : empty ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>Пока нет продуктов.</p>
          <p className="mt-2">Заполните профиль и купите услугу в магазине кабинета.</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/client/onboarding"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
            >
              Профиль компании
            </Link>
            <Link
              href="/client/shop"
              className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
            >
              Магазин услуг
            </Link>
          </div>
        </div>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {orders.map((o) => (
            <li
              key={o.order_id}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                Мой сайт
              </p>
              <p className="mt-1 text-lg font-semibold text-white">
                {o.business_name || "Landing"}
              </p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-emerald-300">
                {o.status_label || o.status || "Active"}
              </p>
              <p className="mt-2 flex-1 text-sm text-zinc-500">
                {o.package_name || "Website"} · заказ {o.order_id}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/order/status/${o.order_id}`}
                  className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                >
                  Открыть
                </Link>
                {o.product_id ? (
                  <a
                    href={`${API}/api/factory/products/${o.product_id}/preview`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-xl border border-emerald-500/40 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-950/40"
                  >
                    Превью сайта
                  </a>
                ) : null}
                {o.download_ready && o.download_url ? (
                  <a
                    href={`${API}${o.download_url}`}
                    className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                  >
                    Скачать ZIP
                  </a>
                ) : (
                  <span className="rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-500">
                    ZIP готовится…
                  </span>
                )}
              </div>
            </li>
          ))}
          {products.map((p) => (
            <li
              key={p.product_id}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-lg font-semibold text-white">{p.display_name}</p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-emerald-300">
                {p.status || "Active"}
              </p>
              <p className="mt-2 flex-1 text-sm text-zinc-500">via {p.source}</p>
              <Link
                href={
                  p.product_type === "chatbot" || p.product_id === "prod_chatbot"
                    ? "/projects/chatbot"
                    : "/client/orders"
                }
                className="mt-4 inline-flex rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
              >
                Открыть
              </Link>
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
