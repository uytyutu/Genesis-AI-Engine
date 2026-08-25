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
import { resolveOrderHonestStatus } from "../lib/clientProductStatus";
import {
  resolveBccPrimaryCards,
  type BccModuleCardModel,
} from "../lib/bccModuleCatalog";
import { signalsFromOrdersAndProducts } from "../lib/clientServiceMarketplace";
import {
  BccPanel,
  BccPrimaryButton,
  BccQuickLink,
  BccSectionHeader,
  BccStatusPill,
  toneFromHonest,
} from "../lib/clientUi";
import {
  LAUNCH_PRICE_HINTS,
  LAUNCH_PURCHASE_ROUTES,
} from "../lib/launchClientUx";

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

type ProductCardModel = BccModuleCardModel;

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

function ProductCard({ card }: { card: ProductCardModel }) {
  const tone = toneFromHonest(card.status.key);
  return (
    <BccPanel active={tone === "active"} className="flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-2xl" aria-hidden>
          {card.icon}
        </p>
        <BccStatusPill tone={tone} label={card.status.label} />
      </div>
      <h3 className="mt-4 text-lg font-semibold tracking-tight text-white">
        {card.title}
      </h3>
      {card.packageLine ? (
        <p className="mt-1 text-sm text-violet-200/90">{card.packageLine}</p>
      ) : card.priceHint ? (
        <p className="mt-1 text-sm text-zinc-500">{card.priceHint}</p>
      ) : (
        <p className="mt-1 text-sm text-zinc-500">Noch nicht in Ihrem Workspace</p>
      )}
      <div className="mt-auto pt-6">
        {card.cta.actionable && card.ctaHref ? (
          <BccPrimaryButton href={card.ctaHref} tone={tone}>
            {card.cta.label}
          </BccPrimaryButton>
        ) : (
          <span className="inline-flex min-h-[44px] items-center rounded-xl border border-white/10 px-4 text-sm text-zinc-500">
            {card.cta.label || "Demnächst"}
          </span>
        )}
      </div>
    </BccPanel>
  );
}

const EMPTY_OFFERS = [
  {
    id: "website",
    icon: "🌐",
    title: "Website",
    price: LAUNCH_PRICE_HINTS.website,
    href: LAUNCH_PURCHASE_ROUTES.website,
    cta: "Website erstellen",
  },
  {
    id: "shop",
    icon: "🛒",
    title: "Online-Shop",
    price: LAUNCH_PRICE_HINTS.shop,
    href: LAUNCH_PURCHASE_ROUTES.shop,
    cta: "Online-Shop erstellen",
  },
  {
    id: "ai",
    icon: "🤖",
    title: "AI Assistant",
    price: LAUNCH_PRICE_HINTS.ai,
    href: LAUNCH_PURCHASE_ROUTES.ai,
    cta: "AI Assistant hinzufügen",
  },
] as const;

/** Secondary Vector teaser — never competes with purchase CTAs. */
function VectorKennenlernenTeaser({ emphasis = false }: { emphasis?: boolean }) {
  return (
    <BccPanel
      className={
        emphasis
          ? "border-emerald-500/20 p-5"
          : "border-emerald-500/15 p-4"
      }
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-300/70">
        {ASSISTANT_NAME}
      </p>
      <h2
        className={
          emphasis
            ? "mt-2 text-lg font-semibold tracking-tight text-white"
            : "mt-1 text-base font-semibold text-white"
        }
      >
        {emphasis ? "Dein Business Assistant" : "Vector kennenlernen"}
      </h2>
      <p className={emphasis ? "mt-2 max-w-2xl text-sm text-zinc-400" : "mt-1 text-sm text-zinc-500"}>
        {emphasis
          ? "Frag mich zu deinem Unternehmen, deiner Website, Analytics oder deinen nächsten Schritten."
          : "Dein Business Assistant hilft dir bei der Auswahl."}
      </p>
    </BccPanel>
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

  const noProduct = products !== null && !hasWebsite && !hasShop && !hasAi;

  const cards: ProductCardModel[] = useMemo(() => {
    const signals = signalsFromOrdersAndProducts({
      orders,
      products: products ?? [],
    });
    return resolveBccPrimaryCards({
      signals,
      websiteOrder: webOrder,
      shopOrder,
      botOrder,
      websiteManageHref: webOrder
        ? `/client/websites/${webOrder.order_id}/admin`
        : hasWebsite
          ? "/client/products"
          : null,
      shopManageHref: shopOrder
        ? `/client/stores/${shopOrder.order_id}/admin`
        : null,
      packageLine: {
        website: webOrder
          ? packageTierLabel(webOrder.package_id, webOrder.package_name)
          : hasWebsite
            ? "Im Workspace"
            : null,
        shop: shopOrder
          ? packageTierLabel(shopOrder.package_id, shopOrder.package_name)
          : null,
        ai: hasAi ? ASSISTANT_NAME : null,
      },
    });
  }, [webOrder, shopOrder, botOrder, hasWebsite, hasAi, orders, products]);

  const recentOrders = orders.slice(0, 4);
  const todayLabel = new Date().toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "short",
  });
  const rawName = displayName.trim();
  const placeholderNames = new Set([
    "моя компания",
    "mein unternehmen",
    "my company",
  ]);
  const hasRealCompanyName =
    Boolean(rawName) && !placeholderNames.has(rawName.toLowerCase());
  const greetingName = hasRealCompanyName ? rawName : "Ihr Unternehmen";

  return (
    <ClientWorkspaceShell
      title="Übersicht"
      compactChrome
      hasStore={hasShop}
    >
      {error ? (
        <p className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {!hasRealCompanyName && !noProduct ? (
        <div className="mb-5 rounded-xl border border-amber-400/25 bg-amber-500/10 px-3 py-3 text-sm text-amber-100/90">
          Unternehmensprofil vervollständigen — dann kann Virtus Core passgenau
          arbeiten.{" "}
          <Link href="/client/onboarding" className="underline text-amber-50">
            Profil öffnen
          </Link>
        </div>
      ) : null}

      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Guten Tag, {greetingName}
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Ihr Business auf einen Blick
          {giftUnlimited ? " · Unbegrenzter Workspace" : ""}
          {" · "}
          {todayLabel}
        </p>
      </header>

      {products === null ? (
        <p className="mb-8 text-sm text-zinc-500">Produkte werden geladen…</p>
      ) : noProduct ? (
        <>
          <section aria-label="Kein Produkt" className="mb-8">
            <BccPanel className="border-violet-400/25 p-6 sm:p-8">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300/80">
                Start
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-white sm:text-2xl">
                Noch kein Produkt aktiviert
              </h2>
              <p className="mt-2 max-w-xl text-sm text-zinc-400">
                Was möchtest du aufbauen? Starte mit einer digitalen Lösung für
                dein Unternehmen.
              </p>
              <ul className="mt-6 grid gap-3 sm:grid-cols-3">
                {EMPTY_OFFERS.map((offer) => (
                  <li key={offer.id}>
                    <BccPrimaryButton href={offer.href} tone="pending">
                      {offer.cta}
                    </BccPrimaryButton>
                  </li>
                ))}
              </ul>
            </BccPanel>
          </section>

          <section aria-label="Empfohlen" className="mb-8">
            <BccSectionHeader title="Empfohlen" />
            <ul className="mt-4 grid gap-4 sm:grid-cols-3">
              {EMPTY_OFFERS.map((offer) => (
                <li key={`rec-${offer.id}`}>
                  <BccPanel className="flex h-full flex-col p-5">
                    <p className="text-2xl" aria-hidden>
                      {offer.icon}
                    </p>
                    <h3 className="mt-3 text-lg font-semibold text-white">
                      {offer.title}
                    </h3>
                    <p className="mt-1 text-sm text-zinc-500">{offer.price}</p>
                    <div className="mt-auto pt-5">
                      <BccPrimaryButton href={offer.href} tone="inactive">
                        Entdecken →
                      </BccPrimaryButton>
                    </div>
                  </BccPanel>
                </li>
              ))}
            </ul>
          </section>

          <section aria-label="Vector kennenlernen" className="mb-8">
            <VectorKennenlernenTeaser />
          </section>
        </>
      ) : (
        <>
          <section aria-label="Meine Produkte" className="mb-8">
            <BccSectionHeader
              title="Meine Produkte"
              actionHref="/client/products"
              actionLabel="Alle →"
            />
            <ul className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {cards.map((card) => (
                <li key={card.id}>
                  <ProductCard card={card} />
                </li>
              ))}
            </ul>
          </section>

          <section aria-label="Vector Business Assistant" className="mb-8">
            <VectorKennenlernenTeaser emphasis />
          </section>

          {hasWebsite && !hasRealCompanyName ? (
            <div className="mb-8">
              <BusinessSetupPanel dark />
            </div>
          ) : null}

          {hasWebsite || hasShop || hasAi ? (
            <div className="mb-8">
              <AiHealthPanel dark />
            </div>
          ) : null}
        </>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <BccPanel className="p-5">
          <BccSectionHeader
            title="Letzte Bestellungen"
            actionHref="/client/orders"
            actionLabel="Alle →"
          />
          {recentOrders.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-500">
              Noch keine Bestellungen. Starten Sie mit Website oder Shop.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {recentOrders.map((o) => {
                const status = resolveOrderHonestStatus(o);
                return (
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
                        </span>
                      </span>
                      <BccStatusPill
                        tone={toneFromHonest(status.key)}
                        label={status.label}
                      />
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </BccPanel>

        <BccPanel className="p-5">
          <BccSectionHeader title="Schnellzugriff" />
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <BccQuickLink href="/client/support" label="Support" />
            </li>
            <li>
              <BccQuickLink href="/client/downloads" label="Downloads / ZIP" />
            </li>
            <li>
              <BccQuickLink href="/client/billing" label="Abrechnung" />
            </li>
            <li>
              <BccQuickLink href="/client/shop" label="Marketplace" />
            </li>
            {hasAi ? (
              <li>
                <BccQuickLink
                  href="/client/inbox"
                  label={
                    openConversations > 0
                      ? `Inbox · ${openConversations} offen`
                      : "Inbox"
                  }
                  highlight
                />
              </li>
            ) : null}
          </ul>
        </BccPanel>
      </div>

      <VectorCoachingToasts />
    </ClientWorkspaceShell>
  );
}
