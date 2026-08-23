"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientWorkspaceShell } from "../components/ClientWorkspaceShell";
import { VectorCoachingToasts } from "../components/VectorCoachingToasts";
import { BusinessSetupPanel } from "../components/BusinessSetupPanel";
import { AiHealthPanel } from "../components/AiHealthPanel";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";

type MyProduct = {
  product_id: string;
  product_type: string;
  display_name: string;
  status: string;
  source: string;
};

type ConversationRow = {
  conversation_id: string;
  status?: string;
  updated_at?: string;
};

type ClientOrder = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  package_id?: string;
  status?: string;
  status_label?: string;
  download_ready?: boolean;
  product_kind?: string;
  primary_role?: string;
  superseded?: boolean;
  quality_state?: string;
};

type CardTone = "active" | "pending" | "inactive" | "soon";

type ProductCardModel = {
  id: string;
  icon: string;
  title: string;
  packageLine: string | null;
  statusLabel: string;
  tone: CardTone;
  ctaLabel: string;
  ctaHref: string;
};

function isWebsiteProduct(p: MyProduct) {
  return p.product_type === "website" || p.product_id === "prod_website";
}

function isChatbotProduct(p: MyProduct) {
  return p.product_type === "chatbot" || p.product_id === "prod_chatbot";
}

function isShopProduct(p: MyProduct) {
  return (
    p.product_type === "store" ||
    p.product_type === "shop" ||
    p.product_id === "prod_store"
  );
}

function isShopOrder(o: ClientOrder) {
  return (
    String(o.product_kind || "") === "shop" ||
    String(o.package_id || "") === "ecommerce_shop"
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

function orderLooksReady(o: ClientOrder): boolean {
  if (o.download_ready) return true;
  const st = String(o.status || "").toLowerCase();
  return ["ready", "completed", "delivered", "active", "done"].includes(st);
}

function orderLooksPending(o: ClientOrder): boolean {
  return Boolean(o.order_id) && !orderLooksReady(o);
}

const TONE_PILL: Record<CardTone, string> = {
  active: "border-emerald-400/35 bg-emerald-500/15 text-emerald-100",
  pending: "border-amber-400/35 bg-amber-500/15 text-amber-100",
  inactive: "border-white/15 bg-white/[0.04] text-zinc-400",
  soon: "border-violet-400/25 bg-violet-500/10 text-violet-200/90",
};

function ProductCard({ card }: { card: ProductCardModel }) {
  const activeSurface =
    card.tone === "active"
      ? "border-violet-500/40 bg-gradient-to-b from-violet-950/40 to-[#0c0a12] shadow-[0_0_40px_-18px_rgba(124,58,237,0.45)]"
      : "border-white/10 bg-white/[0.03]";

  return (
    <article
      className={`flex h-full flex-col rounded-2xl border p-5 ${activeSurface}`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-2xl" aria-hidden>
          {card.icon}
        </p>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${TONE_PILL[card.tone]}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              card.tone === "active"
                ? "bg-emerald-400"
                : card.tone === "pending"
                  ? "bg-amber-400"
                  : card.tone === "soon"
                    ? "bg-violet-400"
                    : "bg-zinc-500"
            }`}
            aria-hidden
          />
          {card.statusLabel}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-semibold tracking-tight text-white">
        {card.title}
      </h3>
      {card.packageLine ? (
        <p className="mt-1 text-sm text-violet-200/90">{card.packageLine}</p>
      ) : (
        <p className="mt-1 text-sm text-zinc-500">Noch nicht in Ihrem Workspace</p>
      )}
      <div className="mt-auto pt-6">
        <Link
          href={card.ctaHref}
          className={`inline-flex min-h-[44px] w-full items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
            card.tone === "active"
              ? "bg-violet-600 text-white shadow-[0_12px_32px_-14px_rgba(124,58,237,0.85)] hover:bg-violet-500"
              : card.tone === "pending"
                ? "border border-amber-400/40 bg-amber-500/15 text-amber-50 hover:bg-amber-500/25"
                : "border border-white/15 bg-white/[0.04] text-zinc-100 hover:border-violet-400/40 hover:bg-violet-500/10"
          }`}
        >
          {card.ctaLabel}
        </Link>
      </div>
    </article>
  );
}

export default function ClientDashboardPage() {
  const router = useRouter();
  const [products, setProducts] = useState<MyProduct[] | null>(null);
  const [orders, setOrders] = useState<ClientOrder[]>([]);
  const [openConversations, setOpenConversations] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [giftUnlimited, setGiftUnlimited] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const owned = await portalFetch<MyProduct[]>("/portal/my-products");
      setProducts(owned);
      if (owned.some(isChatbotProduct)) {
        const list = await portalFetchAllow404<ConversationRow[]>(
          "/portal/chatbot/conversations",
        );
        const open = (list ?? []).filter(
          (c) => c.status === "open" || c.status === "prepared",
        ).length;
        setOpenConversations(open);
      } else {
        setOpenConversations(0);
      }

      if (getClientToken()) {
        const api = publicApiBase();
        const meRes = await fetch(`${api}/api/client/me`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        if (meRes.ok) {
          const me = await meRes.json();
          setGiftUnlimited(Boolean(me.gift_unlimited || me.unlimited));
          setDisplayName(
            String(me.company_display_name || me.company_name || me.name || ""),
          );
        }
        const ordRes = await fetch(`${api}/api/client/orders`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        if (ordRes.ok) {
          const body = await ordRes.json();
          const rows = Array.isArray(body.orders) ? (body.orders as ClientOrder[]) : [];
          setOrders(
            rows.filter(
              (o) =>
                String(o.status || "").toLowerCase() !== "superseded" &&
                o.superseded !== true &&
                String(o.quality_state || "").toUpperCase() !== "ARCHIVED",
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

  const hasWebsite =
    Boolean(webOrder) || (products ?? []).some(isWebsiteProduct);
  const hasShop =
    Boolean(shopOrder) || (products ?? []).some(isShopProduct);
  const hasAi =
    Boolean(botOrder) || (products ?? []).some(isChatbotProduct);

  const cards: ProductCardModel[] = useMemo(() => {
    const website: ProductCardModel = (() => {
      if (webOrder && orderLooksReady(webOrder)) {
        return {
          id: "website",
          icon: "🌐",
          title: "Website",
          packageLine: packageTierLabel(webOrder.package_id, webOrder.package_name),
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Verwalten →",
          ctaHref: `/client/websites/${webOrder.order_id}/admin`,
        };
      }
      if (webOrder && orderLooksPending(webOrder)) {
        return {
          id: "website",
          icon: "🌐",
          title: "Website",
          packageLine: packageTierLabel(webOrder.package_id, webOrder.package_name),
          statusLabel: "In Bearbeitung",
          tone: "pending",
          ctaLabel: "Öffnen →",
          ctaHref: `/client/websites/${webOrder.order_id}/admin`,
        };
      }
      if (hasWebsite && webOrder) {
        return {
          id: "website",
          icon: "🌐",
          title: "Website",
          packageLine: packageTierLabel(webOrder.package_id, webOrder.package_name),
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Verwalten →",
          ctaHref: `/client/websites/${webOrder.order_id}/admin`,
        };
      }
      if (hasWebsite) {
        return {
          id: "website",
          icon: "🌐",
          title: "Website",
          packageLine: "Im Workspace",
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Verwalten →",
          ctaHref: "/client/products",
        };
      }
      return {
        id: "website",
        icon: "🌐",
        title: "Website",
        packageLine: null,
        statusLabel: "Nicht aktiviert",
        tone: "inactive",
        ctaLabel: "Entdecken →",
        ctaHref: "/order?form=1",
      };
    })();

    const shop: ProductCardModel = (() => {
      if (shopOrder && orderLooksReady(shopOrder)) {
        return {
          id: "shop",
          icon: "🛒",
          title: "Online Shop",
          packageLine: packageTierLabel(shopOrder.package_id, shopOrder.package_name),
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Verwalten →",
          ctaHref: `/client/stores/${shopOrder.order_id}/admin`,
        };
      }
      if (shopOrder && orderLooksPending(shopOrder)) {
        return {
          id: "shop",
          icon: "🛒",
          title: "Online Shop",
          packageLine: packageTierLabel(shopOrder.package_id, shopOrder.package_name),
          statusLabel: "In Bearbeitung",
          tone: "pending",
          ctaLabel: "Öffnen →",
          ctaHref: `/client/stores/${shopOrder.order_id}/admin`,
        };
      }
      if (hasShop && shopOrder) {
        return {
          id: "shop",
          icon: "🛒",
          title: "Online Shop",
          packageLine: packageTierLabel(shopOrder.package_id, shopOrder.package_name),
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Verwalten →",
          ctaHref: `/client/stores/${shopOrder.order_id}/admin`,
        };
      }
      return {
        id: "shop",
        icon: "🛒",
        title: "Online Shop",
        packageLine: null,
        statusLabel: "Nicht aktiviert",
        tone: "inactive",
        ctaLabel: "Entdecken →",
        ctaHref: "/order/shop",
      };
    })();

    const ai: ProductCardModel = (() => {
      if (hasAi) {
        return {
          id: "ai",
          icon: "🤖",
          title: "AI Assistant",
          packageLine: ASSISTANT_NAME,
          statusLabel: "Aktiv",
          tone: "active",
          ctaLabel: "Öffnen →",
          ctaHref: "/client/bots",
        };
      }
      return {
        id: "ai",
        icon: "🤖",
        title: "AI Assistant",
        packageLine: null,
        statusLabel: "Nicht aktiviert",
        tone: "inactive",
        ctaLabel: "Entdecken →",
        ctaHref: "/order/bot",
      };
    })();

    return [website, shop, ai];
  }, [webOrder, shopOrder, hasWebsite, hasShop, hasAi]);

  const recentOrders = orders.slice(0, 4);
  const todayLabel = new Date().toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "short",
  });
  const greetingName = displayName.trim() || "Ihr Unternehmen";
  const showSetup = !hasWebsite || !displayName;

  return (
    <ClientWorkspaceShell
      title="Virtus Core Workspace"
      subtitle={`Business Control Center · ${todayLabel}`}
      hasStore={hasShop}
    >
      {error ? (
        <p className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {!displayName ? (
        <div className="mb-5 rounded-xl border border-amber-400/25 bg-amber-500/10 px-3 py-3 text-sm text-amber-100/90">
          Unternehmensprofil vervollständigen — dann kann Virtus Core passgenau
          arbeiten.{" "}
          <Link href="/client/onboarding" className="underline text-amber-50">
            Profil öffnen
          </Link>
        </div>
      ) : null}

      <header className="mb-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-violet-200/80">
          Workspace
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Guten Tag, {greetingName}
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Ihr Business auf einen Blick
          {giftUnlimited ? " · Unlimited Workspace" : ""}
        </p>
      </header>

      <section aria-label="Ihre Produkte" className="mb-8">
        {products === null ? (
          <p className="text-sm text-zinc-500">Produkte werden geladen…</p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {cards.map((card) => (
              <li key={card.id}>
                <ProductCard card={card} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {showSetup ? (
        <div className="mb-8 grid gap-4 lg:grid-cols-2">
          <BusinessSetupPanel dark />
          <AiHealthPanel dark />
        </div>
      ) : hasAi || hasWebsite ? (
        <div className="mb-8">
          <AiHealthPanel dark />
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-zinc-500">
              Letzte Bestellungen
            </h2>
            <Link
              href="/client/orders"
              className="text-sm font-medium text-violet-300 hover:text-violet-100"
            >
              Alle →
            </Link>
          </div>
          {recentOrders.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-500">
              Noch keine Bestellungen. Starten Sie mit Website oder Shop.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {recentOrders.map((o) => (
                <li key={o.order_id}>
                  <Link
                    href={
                      isShopOrder(o)
                        ? `/client/stores/${o.order_id}/admin`
                        : isBotOrder(o)
                          ? "/client/bots"
                          : `/client/websites/${o.order_id}/admin`
                    }
                    className="flex items-center justify-between gap-3 rounded-xl border border-white/8 bg-black/25 px-3 py-3 transition hover:border-violet-400/35"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-white">
                        {o.business_name || o.package_name || o.order_id}
                      </span>
                      <span className="mt-0.5 block text-xs text-zinc-500">
                        {packageTierLabel(o.package_id, o.package_name)}
                        {o.status_label ? ` · ${o.status_label}` : ""}
                      </span>
                    </span>
                    <span
                      className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        orderLooksReady(o)
                          ? TONE_PILL.active
                          : TONE_PILL.pending
                      }`}
                    >
                      {orderLooksReady(o) ? "Bereit" : "Laufend"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-zinc-500">
            Schnellzugriff
          </h2>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <Link
                href="/client/support"
                className="flex min-h-[44px] items-center justify-between rounded-xl border border-white/8 px-3 py-2.5 text-zinc-200 hover:border-violet-400/35"
              >
                <span>Support</span>
                <span className="text-zinc-500">→</span>
              </Link>
            </li>
            <li>
              <Link
                href="/client/downloads"
                className="flex min-h-[44px] items-center justify-between rounded-xl border border-white/8 px-3 py-2.5 text-zinc-200 hover:border-violet-400/35"
              >
                <span>Downloads / ZIP</span>
                <span className="text-zinc-500">→</span>
              </Link>
            </li>
            <li>
              <Link
                href="/client/billing"
                className="flex min-h-[44px] items-center justify-between rounded-xl border border-white/8 px-3 py-2.5 text-zinc-200 hover:border-violet-400/35"
              >
                <span>Billing</span>
                <span className="text-zinc-500">→</span>
              </Link>
            </li>
            <li>
              <Link
                href="/client/shop"
                className="flex min-h-[44px] items-center justify-between rounded-xl border border-white/8 px-3 py-2.5 text-zinc-200 hover:border-violet-400/35"
              >
                <span>Marketplace</span>
                <span className="text-zinc-500">→</span>
              </Link>
            </li>
            {hasAi ? (
              <li>
                <Link
                  href="/client/inbox"
                  className="flex min-h-[44px] items-center justify-between rounded-xl border border-violet-400/25 bg-violet-500/10 px-3 py-2.5 text-violet-50 hover:bg-violet-500/15"
                >
                  <span>
                    Inbox
                    {openConversations > 0
                      ? ` · ${openConversations} offen`
                      : ""}
                  </span>
                  <span className="text-violet-300">→</span>
                </Link>
              </li>
            ) : null}
          </ul>
        </section>
      </div>

      <VectorCoachingToasts />
    </ClientWorkspaceShell>
  );
}
