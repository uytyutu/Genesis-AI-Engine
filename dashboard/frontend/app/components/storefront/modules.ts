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
    id: "standalone",
    priceEur: 499,
    nameKey: "pricing.webStandalone",
    blurbKey: "pricing.webStandaloneBlurb",
    featured: true,
    featureKeys: [
      "pricing.webStandaloneF1",
      "pricing.webStandaloneF2",
      "pricing.webStandaloneF3",
      "pricing.webStandaloneF4",
      "pricing.webStandaloneF5",
      "pricing.webStandaloneF6",
      "pricing.webStandaloneF7",
      "pricing.webStandaloneF8",
    ] as const,
  },
  {
    id: "connected",
    priceEur: 499,
    monthlyEur: 99,
    nameKey: "pricing.webConnected",
    blurbKey: "pricing.webConnectedBlurb",
    featureKeys: [
      "pricing.webConnectedF1",
      "pricing.webConnectedF2",
      "pricing.webConnectedF3",
      "pricing.webConnectedF4",
      "pricing.webConnectedF5",
      "pricing.webConnectedF6",
      "pricing.webConnectedF7",
      "pricing.webConnectedF8",
    ] as const,
  },
] as const;

/** Comparison — ownership vs ecosystem (not Basic/Business/Premium). */
export const WEBSITE_COMPARE_ROWS = [
  { labelKey: "pricing.compareOwnership", standalone: "yes", connected: "yes" },
  { labelKey: "pricing.compareAdmin", standalone: "yes", connected: "yes" },
  { labelKey: "pricing.compareSource", standalone: "yes", connected: "yes" },
  { labelKey: "pricing.compareWorkspace", standalone: "no", connected: "yes" },
  { labelKey: "pricing.compareCrm", standalone: "no", connected: "yes" },
  { labelKey: "pricing.compareAi", standalone: "no", connected: "yes" },
  { labelKey: "pricing.compareAutomation", standalone: "no", connected: "yes" },
  { labelKey: "pricing.compareUpdates", standalone: "paidAddon", connected: "included" },
  { labelKey: "pricing.compareSupport", standalone: "paidAddon", connected: "included" },
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
