/**
 * Gen2 Stage 0 — Service Marketplace catalog (vitrine only).
 * Active / Activate / Coming Soon — no CRM, no fake Connect for unfinished Gen2.
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

/** Services Virtus can sell or partially deliver today — Activate. */
export const MARKETPLACE_LIVE: MarketplaceServiceDef[] = [
  {
    id: "website",
    icon: "🌐",
    name: "Website",
    blurb: "Цифровое лицо компании — путь к звонку или заявке. Workspace включён.",
    badge: "activate",
    activateHref: "/order?form=1",
    openHref: "/client/site",
    priceHint: "499 € Standalone",
    ctaKind: "order",
    includes: [
      "Сайт под нишу · Virtus AI Workspace",
      "Страницы · медиа · тексты · контакты",
      "Базовое SEO · формы · Impressum",
      "Без подписки (Standalone)",
    ],
    detect: "website",
  },
  {
    id: "ai_store",
    icon: "🛒",
    name: "Online Store",
    blurb: "Каталог, корзина и заказы в том же Workspace — без нового сайта.",
    badge: "activate",
    activateHref: "/order/shop",
    openHref: "/client/products",
    priceHint: "299 €",
    ctaKind: "order",
    includes: [
      "Интернет-магазин под нишу",
      "Товары · категории · заказы",
      "Store Admin в /client",
      "Интеграция с существующим проектом",
    ],
    detect: "store",
  },
  {
    id: "digital_employee",
    icon: "🤖",
    name: "AI Chatbot",
    blurb: "Диалоги с клиентами на сайте и в мессенджерах.",
    badge: "activate",
    activateHref: "/order/bot",
    openHref: "/client/bots",
    priceHint: "99 €",
    ctaKind: "order",
    includes: ["Ответы 24/7", "Сбор заявок", "Telegram", "Кабинет настройки"],
    detect: "bot",
  },
  {
    id: "booking",
    icon: "📅",
    name: "Booking System",
    blurb: "Календарь и формы записи — автоматически на вашем сайте.",
    badge: "activate",
    activateHref: "/client/shop",
    openHref: "/client/booking",
    priceHint: "79 €",
    ctaKind: "activate",
    includes: ["Календарь / слоты", "Формы записи", "Интеграция с сайтом"],
  },
  {
    id: "whatsapp_auto",
    icon: "📱",
    name: "WhatsApp Automation",
    blurb: "Уведомления и диалоги в WhatsApp.",
    badge: "activate",
    activateHref: "/client/shop",
    openHref: "/client/whatsapp",
    priceHint: "59 €",
    ctaKind: "activate",
    includes: ["Кнопка на сайте", "Уведомления о заявках", "Сценарии Connected"],
    detect: "social",
  },
  {
    id: "email_automation",
    icon: "📧",
    name: "Email Automation",
    blurb: "Письма и последовательности для клиентов.",
    badge: "activate",
    activateHref: "/client/shop",
    openHref: "/client/email",
    priceHint: "69 €",
    ctaKind: "activate",
    includes: ["SMTP / шаблоны", "Последовательности", "Связка с заявками"],
    detect: "email",
  },
  {
    id: "automation",
    icon: "⚡",
    name: "Automation",
    blurb: "Сценарии между сайтом, заявками и уведомлениями.",
    badge: "activate",
    activateHref: "/order/service/business_automation?form=1",
    openHref: "/client/automations",
    priceHint: "от 69 €",
    ctaKind: "activate",
    includes: ["Бриф и сценарии", "Интеграции", "План внедрения"],
    detect: "automation",
  },
  {
    id: "website_auditor",
    icon: "🔍",
    name: "Website Auditor",
    blurb: "Проверка сайта и понятный план улучшений.",
    badge: "activate",
    activateHref: "/site?service=analysis",
    openHref: "/client/analyses",
    priceHint: "от 149 €",
    ctaKind: "activate",
    includes: ["HTTPS / mobile / SEO", "Контакты и формы", "План ремонта"],
    detect: "auditor",
  },
  {
    id: "seo",
    icon: "📈",
    name: "SEO Optimization",
    blurb: "Оптимизация сайта для поисковых систем.",
    badge: "activate",
    activateHref: "/order/service/seo_audit?form=1",
    priceHint: "От 249 €",
    ctaKind: "activate",
    includes: ["Title · Description · H1", "robots / sitemap", "План правок"],
    detect: "seo",
  },
  {
    id: "domains_ssl",
    icon: "🌍",
    name: "Domains & SSL",
    blurb: "Домен и HTTPS при публикации.",
    badge: "activate",
    activateHref: "/client/domain",
    openHref: "/client/domain",
    priceHint: "С Website",
    ctaKind: "activate",
    includes: ["Помощь с доменом", "SSL / HTTPS", "Публикация"],
    detect: "domain",
  },
  {
    id: "backup",
    icon: "💾",
    name: "Cloud Backup",
    blurb: "Резервные копии проекта.",
    badge: "activate",
    activateHref: "/client/downloads",
    openHref: "/client/downloads",
    priceHint: "В Workspace",
    ctaKind: "activate",
    includes: ["Скачать ZIP", "Сопровождение", "Снижение риска потери данных"],
    detect: "backup",
  },
];

/** Gen2 / Connected — shelf with honest prices; Coming Soon where not live. */
export const MARKETPLACE_SOON: MarketplaceServiceDef[] = [
  {
    id: "crm",
    icon: "👥",
    name: "CRM",
    blurb: "Заявки, клиенты и история в одном месте — интегрируется с сайтом.",
    badge: "coming_soon",
    priceHint: "149 €",
    includes: ["Контакты и сделки", "Воронка", "Связка с формами сайта"],
  },
  {
    id: "connected",
    icon: "🔗",
    name: "Virtus Core Connected",
    blurb: "Экосистема: CRM, AI, автоматизации, аналитика в том же Workspace.",
    badge: "coming_soon",
    priceHint: "499 € + 99 €/мес",
    includes: ["Все модули в одной панели", "Без миграции сайта", "Virtus AI глубже"],
  },
  {
    id: "ai_marketing",
    icon: "🎥",
    name: "AI Campaign Studio",
    blurb: "Кампании и креативы — Coming Soon.",
    badge: "coming_soon",
    priceHint: "Coming Soon",
  },
  {
    id: "inventory",
    icon: "📦",
    name: "Inventory",
    blurb: "Склад и остатки товаров.",
    badge: "coming_soon",
  },
  {
    id: "analytics_pro",
    icon: "📊",
    name: "Analytics Pro",
    blurb: "Глубокая аналитика Connected.",
    badge: "coming_soon",
    priceHint: "В Connected",
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
