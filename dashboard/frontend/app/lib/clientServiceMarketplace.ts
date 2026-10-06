/**
 * Client cabinet marketplace — core sellable ladder only.
 * Prices SSOT: Website 299/599/999 · AI Store Basic 799 · Business Store Coming Soon ·
 * AI Employee 499+99 / 999+199 / 1499+349.
 */

export type MarketplaceBadge = "active" | "activate" | "coming_soon";

export type MarketplaceServiceDef = {
  id: string;
  icon: string;
  name: string;
  blurb: string;
  /** Default when not owned */
  badge: MarketplaceBadge;
  activateHref?: string;
  openHref?: string;
  priceHint?: string;
  /** Value bullets — why buy / what you get */
  includes?: string[];
  /** CTA when activate: "order" | "activate" */
  ctaKind?: "order" | "activate";
  /** How to detect Active from client orders / portal products */
  detect?:
    | "website"
    | "store"
    | "bot"
    | "auditor"
    | "seo"
    | "security"
    | "automation"
    | "social"
    | "email"
    | "analytics"
    | "domain"
    | "backup";
};

/** Live products with honest SSOT prices. */
export const MARKETPLACE_LIVE: MarketplaceServiceDef[] = [
  {
    id: "website",
    icon: "🌐",
    name: "Website",
    blurb: "Fertige Firmenwebsite — Kontakt, Legal, klare Bestellung.",
    badge: "activate",
    activateHref: "/order?form=1",
    openHref: "/client/site",
    priceHint: "299 / 599 / 999 €",
    ctaKind: "order",
    includes: [
      "Basic 299 € · Business 599 € · Premium 999 €",
      "Branche & Marke — fertige Website",
      "Responsive · Kontakt · Legal",
    ],
    detect: "website",
  },
  {
    id: "ai_store",
    icon: "🛒",
    name: "AI Store Basic",
    blurb: "Online-Shop: Katalog, Warenkorb, Shop Admin.",
    badge: "activate",
    activateHref: "/order/shop",
    openHref: "/client/products",
    priceHint: "799 €",
    ctaKind: "order",
    includes: [
      "Katalog · Warenkorb · Shop Admin",
      "Stripe / Versand / E-Mail — Ihre Konten",
      "Einmalig",
    ],
    detect: "store",
  },
  {
    id: "digital_employee",
    icon: "🤖",
    name: "AI Business Assistant",
    blurb: "Digitaler Mitarbeiter — Anfragen 24/7, Leads fertig für Sie.",
    badge: "activate",
    activateHref: "/order/bot",
    openHref: "/client/bots",
    priceHint: "499+99 · 999+199 · 1499+349 €",
    ctaKind: "order",
    includes: [
      "Starter 499 € + 99 €/Monat",
      "Business 999 € + 199 €/Monat",
      "Pro 1499 € + 349 €/Monat",
      "Telegram + Website Chat live",
    ],
    detect: "bot",
  },
  {
    id: "website_auditor",
    icon: "🔍",
    name: "Website Analysis",
    blurb: "Schriftlicher Prüfbericht mit klarem Verbesserungsplan.",
    badge: "activate",
    activateHref: "/site?service=analysis",
    openHref: "/client/analyses",
    priceHint: "149 €",
    ctaKind: "activate",
    includes: ["HTTPS / mobile / SEO", "Kontakte und Formulare", "Plan"],
    detect: "auditor",
  },
  {
    id: "seo",
    icon: "📈",
    name: "SEO Optimization",
    blurb: "Grundlage für bessere Sichtbarkeit in der Suche.",
    badge: "activate",
    activateHref: "/order/service/seo_audit?form=1",
    priceHint: "ab 249 €",
    ctaKind: "activate",
    includes: ["Title · Description · H1", "robots / sitemap", "Plan"],
    detect: "seo",
  },
];

/** Honest Coming Soon — no invented ladder prices. */
export const MARKETPLACE_SOON: MarketplaceServiceDef[] = [
  {
    id: "ai_store_business",
    icon: "🏬",
    name: "AI Store Business",
    blurb: "Shop + Virtus Workspace — noch nicht im Verkauf.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
  {
    id: "crm",
    icon: "👥",
    name: "CRM",
    blurb: "Anfragen und Kunden in einem Ort — Coming Soon.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
  {
    id: "whatsapp_auto",
    icon: "📱",
    name: "WhatsApp",
    blurb: "WhatsApp / Instagram / Messenger — Coming Soon.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
  {
    id: "booking",
    icon: "📅",
    name: "Booking",
    blurb: "Termine und Kalender — Coming Soon.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
  {
    id: "ai_marketing",
    icon: "🎥",
    name: "AI Campaign Studio",
    blurb: "Kampagnen und Kreatives — Coming Soon.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
];

export type OwnedSignals = {
  hasWebsite?: boolean;
  hasStore?: boolean;
  hasBot?: boolean;
  hasSeo?: boolean;
  hasSecurity?: boolean;
  hasAutomation?: boolean;
  hasSocial?: boolean;
  hasAuditor?: boolean;
  hasEmailCommerce?: boolean;
  hasAnalyticsSurface?: boolean;
  hasDomainPublished?: boolean;
  hasBackup?: boolean;
};

export function resolveMarketplaceBadge(
  def: MarketplaceServiceDef,
  owned: OwnedSignals,
): MarketplaceBadge {
  if (def.badge === "coming_soon") return "coming_soon";
  switch (def.detect) {
    case "website":
      return owned.hasWebsite ? "active" : "activate";
    case "store":
      return owned.hasStore ? "active" : "activate";
    case "bot":
      return owned.hasBot ? "active" : "activate";
    case "seo":
      return owned.hasSeo ? "active" : "activate";
    case "security":
      return owned.hasSecurity ? "active" : "activate";
    case "automation":
      return owned.hasAutomation ? "active" : "activate";
    case "social":
      return owned.hasSocial ? "active" : "activate";
    case "auditor":
      return owned.hasAuditor ? "active" : "activate";
    case "email":
      return owned.hasEmailCommerce || owned.hasStore ? "active" : "activate";
    case "analytics":
      return owned.hasAnalyticsSurface || owned.hasWebsite || owned.hasStore
        ? "active"
        : "activate";
    case "domain":
      return owned.hasDomainPublished || owned.hasWebsite ? "active" : "activate";
    case "backup":
      return owned.hasBackup ? "active" : "activate";
    default:
      return def.badge;
  }
}

export function marketplaceHref(
  def: MarketplaceServiceDef,
  badge: MarketplaceBadge,
): string | null {
  if (badge === "coming_soon") return null;
  if (badge === "active") return def.openHref || def.activateHref || null;
  return def.activateHref || null;
}

export function signalsFromOrdersAndProducts(input: {
  orders?: { package_id?: string; product_kind?: string; status?: string; published_at?: string }[];
  products?: { product_type?: string; product_id?: string }[];
}): OwnedSignals {
  const orders = input.orders || [];
  const products = input.products || [];
  const blob = (o: { package_id?: string; product_kind?: string }) =>
    `${o.product_kind || ""} ${o.package_id || ""}`.toLowerCase();

  const hasWebsite =
    products.some(
      (p) => p.product_type === "website" || p.product_id === "prod_website",
    ) ||
    orders.some((o) => {
      const b = blob(o);
      return (
        !b.includes("store") &&
        !b.includes("shop") &&
        !b.includes("bot") &&
        (b.includes("basic") ||
          b.includes("business") ||
          b.includes("premium") ||
          b.includes("landing") ||
          b.includes("website") ||
          !b.trim())
      );
    });

  const hasStore =
    orders.some((o) => {
      const b = blob(o);
      return b.includes("store") || b.includes("shop") || b.includes("ecommerce");
    }) || products.some((p) => (p.product_type || "").includes("store"));

  const hasBot =
    products.some(
      (p) => p.product_type === "chatbot" || p.product_id === "prod_chatbot",
    ) || orders.some((o) => blob(o).includes("bot"));

  const pkg = (id: string) =>
    orders.some((o) => (o.package_id || "").toLowerCase().includes(id));

  return {
    hasWebsite,
    hasStore,
    hasBot,
    hasSeo: pkg("seo"),
    hasSecurity: pkg("security"),
    hasAutomation: pkg("automation"),
    hasSocial: pkg("social") || pkg("ai_social"),
    hasAuditor: pkg("analysis") || pkg("auditor"),
    hasEmailCommerce: hasStore,
    hasAnalyticsSurface: hasWebsite || hasStore,
    hasDomainPublished: orders.some((o) => Boolean(o.published_at)),
    hasBackup: pkg("maintenance") || pkg("backup"),
  };
}
