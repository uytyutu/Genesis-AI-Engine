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
  action: "websites" | "bots" | "analysis" | "vector" | "order" | "orderBot" | "store" | null;
  /** Optional channel honesty lines (assistant card) */
  availableChannelsKey?: string;
  comingSoonChannelsKey?: string;
};

/** First row — growth path live products (Website · Store · Digital Employee). */
export const STORE_MODULES_PRIMARY: StoreModule[] = [
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
    id: "store",
    icon: "🛒",
    status: "live",
    badge: "new",
    nameKey: "modules.store.name",
    blurbKey: "modules.store.blurb",
    rating: 5,
    action: "store",
  },
  {
    id: "assistant",
    icon: "🤖",
    status: "live",
    badge: "choice",
    nameKey: "modules.assistant.name",
    blurbKey: "modules.assistant.blurb",
    rating: 5,
    action: "bots",
    availableChannelsKey: "modules.assistant.availableToday",
    comingSoonChannelsKey: "modules.assistant.comingSoon",
  },
];

/** Secondary / Coming Soon — lower on the page, not the main purchase decision. */
export const STORE_MODULES_SOON: StoreModule[] = [
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
];

/** @deprecated use STORE_MODULES_PRIMARY + STORE_MODULES_SOON */
export const STORE_MODULES: StoreModule[] = [
  ...STORE_MODULES_PRIMARY,
  ...STORE_MODULES_SOON,
];

export const WEBSITE_PRICE_TIERS = [
  {
    id: "basic",
    priceEur: 299,
    nameKey: "pricing.webBasic",
    blurbKey: "pricing.webBasicBlurb",
    featureKeys: [
      "pricing.webBasicF1",
      "pricing.webBasicF2",
      "pricing.webBasicF3",
      "pricing.webBasicF4",
      "pricing.webBasicF5",
      "pricing.webBasicF6",
      "pricing.webBasicF7",
      "pricing.webBasicF8",
      "pricing.webBasicF9",
      "pricing.webBasicF10",
    ] as const,
  },
  {
    id: "business",
    priceEur: 599,
    nameKey: "pricing.webBusiness",
    blurbKey: "pricing.webBusinessBlurb",
    featured: true,
    featureKeys: [
      "pricing.webBusinessF1",
      "pricing.webBusinessF2",
      "pricing.webBusinessF3",
      "pricing.webBusinessF4",
      "pricing.webBusinessF5",
      "pricing.webBusinessF6",
      "pricing.webBusinessF7",
      "pricing.webBusinessF8",
      "pricing.webBusinessF9",
    ] as const,
  },
  {
    id: "premium",
    priceEur: 999,
    nameKey: "pricing.webPremium",
    blurbKey: "pricing.webPremiumBlurb",
    featureKeys: [
      "pricing.webPremiumF1",
      "pricing.webPremiumF2",
      "pricing.webPremiumF3",
      "pricing.webPremiumF4",
      "pricing.webPremiumF5",
      "pricing.webPremiumF6",
      "pricing.webPremiumF7",
      "pricing.webPremiumF8",
      "pricing.webPremiumF9",
      "pricing.webPremiumF10",
      "pricing.webPremiumF11",
    ] as const,
  },
] as const;

/** Comparison rows for Basic / Business / Premium (commercial matrix). */
export const WEBSITE_COMPARE_ROWS = [
  { labelKey: "pricing.compareModern", basic: "yes", business: "yes", premium: "yes" },
  { labelKey: "pricing.compareResponsive", basic: "yes", business: "yes", premium: "yes" },
  {
    labelKey: "pricing.comparePresentation",
    basic: "no",
    business: "yes",
    premium: "yes",
  },
  { labelKey: "pricing.compareAdmin", basic: "no", business: "yes", premium: "yes" },
  {
    labelKey: "pricing.compareExtendedControl",
    basic: "no",
    business: "no",
    premium: "yes",
  },
  {
    labelKey: "pricing.compareDeepStructure",
    basic: "no",
    business: "no",
    premium: "yes",
  },
  {
    labelKey: "pricing.compareExtendedForms",
    basic: "no",
    business: "no",
    premium: "yes",
  },
  {
    labelKey: "pricing.compareAdvancedMgmt",
    basic: "no",
    business: "no",
    premium: "yes",
  },
  { labelKey: "pricing.compareSeo", basic: "yes", business: "yes", premium: "seoPro" },
  { labelKey: "pricing.compareAnalytics", basic: "no", business: "yes", premium: "yes" },
  { labelKey: "pricing.compareVector", basic: "no", business: "no", premium: "yes" },
  { labelKey: "pricing.compareSupport", basic: "no", business: "no", premium: "yes" },
] as const;


/** DE anchors — must match pricing_engine BOT_DE_ANCHORS (setup + monthly). */
export const CHATBOT_PRICE_TIERS = [
  {
    id: "bot_starter",
    setupEur: 499,
    monthlyEur: 99,
    nameKey: "pricing.botStarter",
    blurbKey: "pricing.botStarterBlurb",
    outcomeKeys: [
      "pricing.botOutcome24",
      "pricing.botOutcomeLeads",
      "pricing.botOutcomeNoManager",
    ] as const,
  },
  {
    id: "bot_business",
    setupEur: 999,
    monthlyEur: 199,
    nameKey: "pricing.botBusiness",
    blurbKey: "pricing.botBusinessBlurb",
    featured: true,
    outcomeKeys: [
      "pricing.botOutcome24",
      "pricing.botOutcomeBooking",
      "pricing.botOutcomeMulti",
      "pricing.botOutcomeHours",
    ] as const,
  },
  {
    id: "bot_professional",
    setupEur: 1499,
    monthlyEur: 349,
    nameKey: "pricing.botPro",
    blurbKey: "pricing.botProBlurb",
    outcomeKeys: [
      "pricing.botOutcomeTeam",
      "pricing.botOutcomeRoi",
      "pricing.botOutcomeVip",
      "pricing.botOutcomeScale",
    ] as const,
  },
] as const;
