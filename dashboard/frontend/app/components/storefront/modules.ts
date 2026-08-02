/** App Store catalog — LIVE vs Coming Soon (honest). */

export type StoreModuleStatus = "live" | "soon";

export type StoreModuleBadge = "popular" | "new" | "choice" | null;

export type StoreModule = {
  id: string;
  icon: string;
  status: StoreModuleStatus;
  badge: StoreModuleBadge;
  /** i18n key under appStore.modules.<id> */
  nameKey: string;
  blurbKey: string;
  rating: number;
  /** Primary action when live */
  action: "websites" | "bots" | "analysis" | "vector" | "order" | "orderBot" | null;
};

export const STORE_MODULES: StoreModule[] = [
  {
    id: "website",
    icon: "🌐",
    status: "live",
    badge: "popular",
    nameKey: "modules.website.name",
    blurbKey: "modules.website.blurb",
    rating: 5,
    action: "websites",
  },
  {
    id: "receptionist",
    icon: "🤖",
    status: "live",
    badge: "choice",
    nameKey: "modules.receptionist.name",
    blurbKey: "modules.receptionist.blurb",
    rating: 5,
    action: "bots",
  },
  {
    id: "chatbot",
    icon: "💬",
    status: "live",
    badge: "new",
    nameKey: "modules.chatbot.name",
    blurbKey: "modules.chatbot.blurb",
    rating: 5,
    action: "bots",
  },
  {
    id: "audit",
    icon: "📈",
    status: "live",
    badge: null,
    nameKey: "modules.audit.name",
    blurbKey: "modules.audit.blurb",
    rating: 5,
    action: "analysis",
  },
  {
    id: "instagram",
    icon: "📸",
    status: "soon",
    badge: null,
    nameKey: "modules.instagram.name",
    blurbKey: "modules.instagram.blurb",
    rating: 0,
    action: null,
  },
  {
    id: "whatsapp",
    icon: "💚",
    status: "soon",
    badge: null,
    nameKey: "modules.whatsapp.name",
    blurbKey: "modules.whatsapp.blurb",
    rating: 0,
    action: null,
  },
  {
    id: "telegram",
    icon: "✈️",
    status: "soon",
    badge: null,
    nameKey: "modules.telegram.name",
    blurbKey: "modules.telegram.blurb",
    rating: 0,
    action: null,
  },
  {
    id: "booking",
    icon: "📅",
    status: "soon",
    badge: null,
    nameKey: "modules.booking.name",
    blurbKey: "modules.booking.blurb",
    rating: 0,
    action: null,
  },
  {
    id: "crm",
    icon: "🗂️",
    status: "soon",
    badge: null,
    nameKey: "modules.crm.name",
    blurbKey: "modules.crm.blurb",
    rating: 0,
    action: null,
  },
  {
    id: "analytics",
    icon: "📊",
    status: "soon",
    badge: null,
    nameKey: "modules.analytics.name",
    blurbKey: "modules.analytics.blurb",
    rating: 0,
    action: null,
  },
];

export const WEBSITE_PRICE_TIERS = [
  { id: "basic", priceEur: 350, nameKey: "pricing.webBasic", blurbKey: "pricing.webBasicBlurb" },
  { id: "business", priceEur: 650, nameKey: "pricing.webBusiness", blurbKey: "pricing.webBusinessBlurb", featured: true },
  { id: "premium", priceEur: 1200, nameKey: "pricing.webPremium", blurbKey: "pricing.webPremiumBlurb" },
] as const;

/** DE anchors — must match pricing_engine BOT_DE_ANCHORS (setup + monthly). */
export const CHATBOT_PRICE_TIERS = [
  {
    id: "bot_starter",
    setupEur: 499,
    monthlyEur: 99,
    nameKey: "pricing.botStarter",
    blurbKey: "pricing.botStarterBlurb",
  },
  {
    id: "bot_business",
    setupEur: 999,
    monthlyEur: 199,
    nameKey: "pricing.botBusiness",
    blurbKey: "pricing.botBusinessBlurb",
    featured: true,
  },
  {
    id: "bot_professional",
    setupEur: 1499,
    monthlyEur: 349,
    nameKey: "pricing.botPro",
    blurbKey: "pricing.botProBlurb",
  },
] as const;
