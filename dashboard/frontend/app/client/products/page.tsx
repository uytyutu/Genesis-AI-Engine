"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import {
  resolveBccModuleCards,
  type BccModuleCardModel,
} from "../../lib/bccModuleCatalog";
import { resolveOrderHonestStatus } from "../../lib/clientProductStatus";
import { signalsFromOrdersAndProducts } from "../../lib/clientServiceMarketplace";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { publicApiBase } from "../../lib/publicApiBase";
import {
  BccPanel,
  BccPrimaryButton,
  BccSectionHeader,
  BccStatusPill,
  toneFromHonest,
} from "../../lib/clientUi";

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
  primary_role?: string;
  superseded?: boolean;
  quality_state?: string;
};

function isShopOrder(o: ClientOrder) {
  return (
    o.product_kind === "shop" || o.package_id === "ecommerce_shop"
  );
}

function isBotOrder(o: ClientOrder) {
  return String(o.product_kind || "").startsWith("bot");
}

function isWebsiteOrder(o: ClientOrder) {
  return !isShopOrder(o) && !isBotOrder(o);
}

function preferPrimary(rows: ClientOrder[]): ClientOrder | null {
  if (rows.length === 0) return null;
  return (
    rows.find((o) => String(o.primary_role || "").toLowerCase() === "primary") ||
    rows[0] ||
    null
  );
}

function packageTierLabel(packageId: string | undefined, packageName?: string): string {
  const id = String(packageId || "").toLowerCase();
  if (id === "basic") return "Basic";
  if (id === "business" || id === "standalone") return "Business";
  if (id === "premium" || id === "connected") return "Premium";
  if (id === "ecommerce_shop") return "AI Store";
  const name = String(packageName || "").replace(/^Landing\s+/i, "").trim();
  return name || "Paket";
}

function ModuleCard({ card }: { card: BccModuleCardModel }) {
  const tone = toneFromHonest(card.status.key);
  return (
    <BccPanel active={tone === "active"} className="flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-2">
        <p className="text-2xl" aria-hidden>
          {card.icon}
        </p>
        <BccStatusPill tone={tone} label={card.status.label} />
      </div>
      <p className="mt-3 text-lg font-semibold text-white">{card.title}</p>
      {card.packageLine ? (
        <p className="mt-1 text-sm text-violet-200/90">{card.packageLine}</p>
      ) : card.priceHint ? (
        <p className="mt-1 text-sm font-medium text-emerald-200/90">
          {card.priceHint}
        </p>
      ) : card.status.key === "coming_soon" ? (
        <p className="mt-1 text-sm text-zinc-500">Noch nicht verfügbar</p>
      ) : card.status.key === "active" || card.status.key === "pending" ? (
        <p className="mt-1 text-sm text-zinc-500">Im Workspace</p>
      ) : (
        <p className="mt-1 text-sm text-zinc-500">Noch nicht in Ihrem Workspace</p>
      )}
      <div className="mt-auto pt-5">
        {card.cta.actionable && card.ctaHref ? (
          <BccPrimaryButton href={card.ctaHref} tone={tone}>
            {card.cta.label}
          </BccPrimaryButton>
        ) : (
          <span className="inline-flex min-h-[44px] items-center rounded-xl border border-white/10 px-4 text-sm text-zinc-500">
            {card.cta.label || "Coming Soon"}
          </span>
        )}
      </div>
    </BccPanel>
  );
}

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
              (o: ClientOrder) => {
                const st = String(o.status || "").toLowerCase();
                if (st === "superseded") return false;
                if (o.superseded === true) return false;
                if (String(o.quality_state || "").toUpperCase() === "ARCHIVED") {
                  return false;
                }
                return true;
              },
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

  const webOrder = useMemo(
    () => preferPrimary(orders.filter(isWebsiteOrder)),
    [orders],
  );
  const shopOrder = useMemo(
    () => preferPrimary(orders.filter(isShopOrder)),
    [orders],
  );
  const botOrder = useMemo(
    () => preferPrimary(orders.filter(isBotOrder)),
    [orders],
  );

  const catalogCards = useMemo(() => {
    const signals = signalsFromOrdersAndProducts({
      orders,
      products: products ?? [],
    });
    return resolveBccModuleCards({
      signals,
      websiteOrder: webOrder,
      shopOrder,
      botOrder,
      websiteManageHref: webOrder
        ? `/client/websites/${webOrder.order_id}/admin`
        : signals.hasWebsite
          ? "/client/site"
          : null,
      shopManageHref: shopOrder
        ? `/client/stores/${shopOrder.order_id}/admin`
        : null,
      packageLine: {
        website: webOrder
          ? packageTierLabel(webOrder.package_id, webOrder.package_name)
          : signals.hasWebsite
            ? "Im Workspace"
            : null,
        shop: shopOrder
          ? packageTierLabel(shopOrder.package_id, shopOrder.package_name)
          : null,
        ai: signals.hasBot ? "Virtus AI" : null,
      },
    });
  }, [orders, products, webOrder, shopOrder, botOrder]);

  const ownedOrders = orders.filter((o) => !isBotOrder(o));

  return (
    <ClientWorkspaceShell
      title="Meine Produkte"
      subtitle="Product Control — Aktiv verwalten, fehlende Module hinzufügen, Coming Soon nur wenn noch nicht lieferbar."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}

      {products === null ? (
        <p className="text-sm text-zinc-500">Laden…</p>
      ) : (
        <>
          <BccSectionHeader title="Module" />
          <ul className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {catalogCards.map((card) => (
              <li key={card.id}>
                <ModuleCard card={card} />
              </li>
            ))}
          </ul>

          {ownedOrders.length > 0 ? (
            <div className="mt-10">
              <BccSectionHeader title="Aufträge & Downloads" />
              <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                {ownedOrders.map((o) => {
                  const status = resolveOrderHonestStatus(o);
                  const shop = isShopOrder(o);
                  return (
                    <li key={o.order_id}>
                      <BccPanel
                        active={status.key === "active"}
                        className="flex h-full flex-col p-5"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                            {shop ? "Online Shop" : "Website"}
                          </p>
                          <BccStatusPill
                            tone={toneFromHonest(status.key)}
                            label={status.label}
                          />
                        </div>
                        <p className="mt-2 text-lg font-semibold text-white">
                          {shop
                            ? o.service_name || o.package_name || "Mein Online Shop"
                            : o.service_name ||
                              o.package_name ||
                              o.business_name ||
                              "Auftrag"}
                        </p>
                        <p className="mt-2 flex-1 text-sm text-zinc-500">
                          {o.business_name ? `${o.business_name} · ` : ""}
                          {o.order_id}
                          {o.eta_label ? ` · ETA ${o.eta_label}` : ""}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <Link
                            href={
                              shop
                                ? `/client/stores/${o.order_id}/admin`
                                : `/client/websites/${o.order_id}/admin`
                            }
                            className="rounded-xl bg-violet-600 px-3 py-2 text-sm font-semibold text-white hover:bg-violet-500"
                          >
                            Verwalten
                          </Link>
                          <Link
                            href={`/order/status/${o.order_id}`}
                            className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                          >
                            Status
                          </Link>
                          {o.product_id ? (
                            <a
                              href={`${API}/api/factory/products/${o.product_id}/preview`}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-xl border border-violet-500/40 px-3 py-2 text-sm text-violet-100 hover:bg-violet-950/40"
                            >
                              Vorschau
                            </a>
                          ) : null}
                          {o.download_ready && o.download_url ? (
                            <a
                              href={`${API}${o.download_url}`}
                              className="rounded-xl border border-emerald-500/40 px-3 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-950/30"
                            >
                              ZIP laden
                            </a>
                          ) : (
                            <span className="rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-500">
                              {shop
                                ? o.shop_pipeline_label ||
                                  o.download_label ||
                                  "In Arbeit…"
                                : o.download_label || "ZIP bald verfügbar"}
                            </span>
                          )}
                        </div>
                      </BccPanel>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}
        </>
      )}
    </ClientWorkspaceShell>
  );
}
