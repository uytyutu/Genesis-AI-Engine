/**
 * Gen2 Stage 0 — Service Marketplace catalog (vitrine only).
 * BCC 2.0: live = real order/delivery path; everything else = Coming Soon.
 * No fake Activate loops to /client/shop stubs.
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
  includes?: string[];
  ctaKind?: "order" | "activate";
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

/** Truly purchasable / usable today. */
export const MARKETPLACE_LIVE: MarketplaceServiceDef[] = [
  {
    id: "website",
    icon: "🌐",
    name: "Website",
    blurb:
      "Digitale Visitenkarte Ihres Unternehmens — Weg zu Anruf oder Anfrage. Workspace inklusive.",
    badge: "activate",
    activateHref: "/order?form=1",
    openHref: "/client/site",
    priceHint: "Ab 199 €",
    ctaKind: "order",
    includes: [
      "Website nach Branche · Virtus AI Workspace",
      "Seiten · Medien · Texte · Kontakte",
      "Basis-SEO · Formulare · Impressum",
      "Ohne Abo (Standalone)",
    ],
    detect: "website",
  },
  {
    id: "ai_store",
    icon: "🛒",
    name: "Online Store",
    blurb:
      "Katalog, Warenkorb und Bestellungen im selben Workspace — ohne neue Website.",
    badge: "activate",
    activateHref: "/order/shop",
    openHref: "/client/products",
    priceHint: "Ab 799 €",
    ctaKind: "order",
    includes: [
      "Onlineshop nach Branche",
      "Produkte · Kategorien · Bestellungen",
      "Store Admin unter /client",
      "Integration in bestehendes Projekt",
    ],
    detect: "store",
  },
  {
    id: "digital_employee",
    icon: "🤖",
    name: "AI Chatbot",
    blurb: "Kundendialoge auf der Website und in Messengern.",
    badge: "activate",
    activateHref: "/order/bot",
    openHref: "/client/bots",
    priceHint: "Ab 499 €",
    ctaKind: "order",
    includes: ["Antworten 24/7", "Lead-Erfassung", "Telegram", "Setup-Bereich"],
    detect: "bot",
  },
  {
    id: "website_auditor",
    icon: "🔍",
    name: "Website Auditor",
    blurb: "Website-Check und klarer Verbesserungsplan.",
    badge: "activate",
    activateHref: "/site?service=analysis",
    openHref: "/client/analyses",
    priceHint: "Kostenloser Check",
    ctaKind: "order",
    includes: ["HTTPS / Mobile / SEO", "Kontakte und Formulare", "Reparaturplan"],
    detect: "auditor",
  },
  {
    id: "backup",
    icon: "💾",
    name: "Cloud Backup",
    blurb: "ZIP und Sicherungen Ihres Projekts im Workspace.",
    badge: "activate",
    activateHref: "/client/downloads",
    openHref: "/client/downloads",
    priceHint: "Im Workspace",
    ctaKind: "activate",
    includes: [
      "ZIP herunterladen",
      "Begleitung",
      "Weniger Risiko durch Datenverlust",
    ],
    detect: "backup",
  },
];

/** Not deliverable yet — Coming Soon (no Hinzufügen / Aktivieren). */
export const MARKETPLACE_SOON: MarketplaceServiceDef[] = [
  {
    id: "booking",
    icon: "📅",
    name: "Booking System",
    blurb: "Kalender und Buchungsformulare auf Ihrer Website.",
    badge: "coming_soon",
  },
  {
    id: "whatsapp_auto",
    icon: "📱",
    name: "WhatsApp Automation",
    blurb: "Benachrichtigungen und Dialoge in WhatsApp.",
    badge: "coming_soon",
  },
  {
    id: "email_automation",
    icon: "📧",
    name: "Email Automation",
    blurb: "E-Mails und Sequenzen für Ihre Kunden.",
    badge: "coming_soon",
  },
  {
    id: "automation",
    icon: "⚡",
    name: "Automation",
    blurb: "Abläufe zwischen Website, Anfragen und Benachrichtigungen.",
    badge: "coming_soon",
  },
  {
    id: "seo",
    icon: "📈",
    name: "SEO Optimization",
    blurb: "Optimierung Ihrer Website für Suchmaschinen.",
    badge: "coming_soon",
  },
  {
    id: "domains_ssl",
    icon: "🌍",
    name: "Domains & SSL",
    blurb: "Eigene Domain und HTTPS bei der Veröffentlichung.",
    badge: "coming_soon",
  },
  {
    id: "crm",
    icon: "👥",
    name: "CRM",
    blurb:
      "Anfragen, Kunden und Historie an einem Ort — verbunden mit der Website.",
    badge: "coming_soon",
  },
  {
    id: "connected",
    icon: "🔗",
    name: "Virtus Core Connected",
    blurb:
      "Ökosystem: CRM, AI, Automation, Analytics im selben Workspace.",
    badge: "coming_soon",
  },
  {
    id: "ai_marketing",
    icon: "🎥",
    name: "AI Campaign Studio",
    blurb: "Kampagnen und Creatives.",
    badge: "coming_soon",
  },
  {
    id: "inventory",
    icon: "📦",
    name: "Inventory",
    blurb: "Lager und Bestände für Produkte.",
    badge: "coming_soon",
  },
  {
    id: "analytics_pro",
    icon: "📊",
    name: "Analytics",
    blurb: "Echte Besucher- und Umsatzdaten nach angebundener Quelle.",
    badge: "coming_soon",
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
      return owned.hasBackup || owned.hasWebsite ? "active" : "activate";
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
  orders?: {
    package_id?: string;
    product_kind?: string;
    status?: string;
    published_at?: string;
  }[];
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
    hasAnalyticsSurface: false,
    hasDomainPublished: orders.some((o) => Boolean(o.published_at)),
    hasBackup: pkg("maintenance") || pkg("backup"),
  };
}
