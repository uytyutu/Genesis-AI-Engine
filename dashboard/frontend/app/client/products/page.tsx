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
  service_name?: string;
  status_label?: string;
  status?: string;
  download_ready?: boolean;
  download_url?: string | null;
  download_label?: string | null;
  product_kind?: string;
  product_id?: string | null;
  eta_label?: string | null;
  billing?: string;
  shop_pipeline?: string | null;
  shop_pipeline_label?: string | null;
  store_url?: string | null;
  package_id?: string;
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
            body.orders.filter((o: ClientOrder) => {
              const kind = String(o.product_kind || "");
              return !kind.startsWith("bot");
            }),
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
      subtitle="Сайты и Website Services в кабинете. Скачивание — когда результат готов."
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
                {o.product_kind === "shop" || o.package_id === "ecommerce_shop"
                  ? "AI Store"
                  : o.product_kind === "addon" || o.product_kind === "repair"
                    ? "Website Service"
                    : "Мой сайт"}
              </p>
              <p className="mt-1 text-lg font-semibold text-white">
                {o.product_kind === "shop"
                  ? o.service_name || o.package_name || "Мой интернет-магазин"
                  : o.service_name || o.package_name || o.business_name || "Заказ"}
              </p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-emerald-300">
                {o.shop_pipeline_label ||
                  o.status_label ||
                  o.status ||
                  "Active"}
              </p>
              <p className="mt-2 flex-1 text-sm text-zinc-500">
                {o.business_name ? `${o.business_name} · ` : ""}
                заказ {o.order_id}
                {o.eta_label ? ` · ETA ${o.eta_label}` : ""}
                {o.billing === "monthly" ? " · первый месяц" : ""}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {o.product_kind === "shop" || o.package_id === "ecommerce_shop" ? (
                  <Link
                    href={o.store_url || `/client/stores/${o.order_id}`}
                    className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                  >
                    Открыть магазин
                  </Link>
                ) : (
                  <>
                    <Link
                      href={`/client/websites/${o.order_id}/admin`}
                      className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                    >
                      Website Admin
                    </Link>
                    <Link
                      href={`/order/status/${o.order_id}`}
                      className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                    >
                      Статус
                    </Link>
                  </>
                )}
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
                    Скачать
                  </a>
                ) : o.product_kind !== "shop" ? (
                  <span className="rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-500">
                    {o.download_label || "В работе…"}
                    {o.eta_label ? ` · ${o.eta_label}` : ""}
                  </span>
                ) : (
                  <span className="rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-500">
                    {o.shop_pipeline_label || o.download_label || "В работе…"}
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
