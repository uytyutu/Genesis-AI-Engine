/**
 * Commercial catalog — public Website / Online-Shop ladder.
 * Keep in sync with dashboard/backend commercial_catalog_g23 + pricing_engine.
 */

export type CommercialCategory = "one_time" | "monthly" | "product";
export type CommercialCta = "order_now" | "activate" | "coming_soon";
export type CatalogGroupId =
  | "websites"
  | "stores"
  | "automation"
  | "chatbots"
  | "marketing"
  | "bots"
  | "website_services";

export type CommercialRow = {
  id: string;
  category: CommercialCategory;
  name: string;
  price_label: string;
  billing: "one_time" | "monthly";
  availability: "available" | "coming_soon";
  cta: CommercialCta;
  cta_href?: string;
  cta_label: string;
  includes: string;
  group?: CatalogGroupId;
};

/** Public Website ladder — same amounts on /site, /order, checkout. */
export const LANDING_PACKAGES_EUR = {
  basic: 299,
  business: 599,
  premium: 999,
  // Legacy API aliases (not shown as separate products)
  standalone: 599,
  connected: 999,
  connected_monthly: 0,
} as const;

export const PRODUCT_SHOWCASE_GROUPS: {
  id: CatalogGroupId;
  title: string;
  blurb: string;
}[] = [
  {
    id: "websites",
    title: "Business websites",
    blurb: "Ready digital solutions for a real company — not templates.",
  },
  {
    id: "stores",
    title: "Online stores",
    blurb: "By industry — Fashion, Beauty, Electronics, and more.",
  },
  {
    id: "chatbots",
    title: "AI chatbots",
    blurb: "Role-based digital employees for sales, booking, support.",
  },
  {
    id: "automation",
    title: "Automation",
    blurb: "CRM, WhatsApp, booking, invoices — Connected ecosystem.",
  },
  {
    id: "marketing",
    title: "Marketing",
    blurb: "Coming soon — Reels, ads, SEO content.",
  },
  {
    id: "website_services",
    title: "Website services",
    blurb: "Repair, SEO, migration — order form first.",
  },
];

export const COMMERCIAL_CATALOG: CommercialRow[] = [
  {
    id: "website_basic",
    category: "product",
    group: "websites",
    name: "Website Basic",
    price_label: `${LANDING_PACKAGES_EUR.basic} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=basic",
    cta_label: "Website Basic wählen",
    includes: "Fertige Website · Kontakt · Legal · ohne Virtus Workspace",
  },
  {
    id: "website_business",
    category: "product",
    group: "websites",
    name: "Website Business",
    price_label: `${LANDING_PACKAGES_EUR.business} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=business",
    cta_label: "Website Business wählen",
    includes: "Alles aus Basic + Virtus Client Workspace",
  },
  {
    id: "website_premium",
    category: "product",
    group: "websites",
    name: "Website Premium",
    price_label: `${LANDING_PACKAGES_EUR.premium} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=premium",
    cta_label: "Website Premium wählen",
    includes:
      "Same visual quality as Business · Connected path · deeper control not proven day-1",
  },
  {
    id: "ai_store",
    category: "product",
    group: "stores",
    name: "AI Store Basic / Start",
    price_label: "799 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/shop",
    cta_label: "Order AI Store Basic",
    includes:
      "Catalog · cart · Shop Admin day-1 · Stripe/SMTP/Shipping via owner accounts",
  },
  {
    id: "ai_store_business",
    category: "product",
    group: "stores",
    name: "AI Store Business",
    price_label: "Coming soon · price TBD",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_label: "Coming soon",
    includes:
      "Shop + Virtus Workspace · manage · grow · add-ons — not for sale yet",
  },
  {
    id: "ai_business_bot",
    category: "product",
    group: "chatbots",
    name: "AI Digital Employee",
    price_label: "499–1499 € setup + 99–349 €/mo",
    billing: "monthly",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/bot",
    cta_label: "Order",
    includes:
      "Live today: Telegram + Website Chat · WhatsApp / Instagram / Messenger — Coming Soon",
  },
  {
    id: "ai_website_analysis",
    category: "one_time",
    group: "website_services",
    name: "Written AI analysis report",
    price_label: "149 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/service/ai_website_analysis",
    cta_label: "Order form",
    includes: "Free check on /site · paid written report 149 € via form",
  },
  {
    id: "website_repair",
    category: "one_time",
    group: "website_services",
    name: "Website Repair",
    price_label: "from 199 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/service/website_repair",
    cta_label: "Order form",
    includes: "Broken site? Recovery target 24–48h · form → payment",
  },
];

/** Niche solution chips for the vitrine (mirrors backend solution_catalog). */
export const WEBSITE_SOLUTION_CHIPS: { id: string; label: string; niche: string }[] = [
  { id: "kosmetikstudio", label: "Nail · Brow · Lash · Massage", niche: "beauty" },
  { id: "friseur", label: "Friseur", niche: "beauty" },
  { id: "reinigung", label: "Reinigung", niche: "cleaning" },
  { id: "it_service", label: "Computer-Reparatur", niche: "computer" },
  { id: "zahnarzt", label: "Zahnarzt", niche: "dental" },
  { id: "restaurant", label: "Restaurant", niche: "restaurant" },
  { id: "handwerk", label: "Handwerk & Renovierung", niche: "handwerk" },
  { id: "elektriker", label: "Elektriker", niche: "handwerk" },
  { id: "autowerkstatt", label: "Autowerkstatt", niche: "auto" },
  { id: "dachreinigung", label: "Dachreinigung", niche: "dachreinigung" },
  { id: "gartenbau", label: "Gartenbau", niche: "gartenpflege" },
  { id: "psychologie", label: "Psychologie", niche: "psychology" },
  { id: "pizzeria", label: "Pizzeria", niche: "restaurant" },
  { id: "rechtsanwalt", label: "Rechtsanwalt", niche: "law" },
  { id: "immobilienmakler", label: "Immobilienmakler", niche: "realestate" },
  { id: "fitnessstudio", label: "Fitnessstudio", niche: "fitness" },
  { id: "fotograf", label: "Fotograf", niche: "photography" },
];

export const STORE_SOLUTION_CHIPS: { id: string; label: string }[] = [
  { id: "beauty_store", label: "Beauty / Pflege (LUMIA)" },
  { id: "fashion", label: "Fashion Store" },
  { id: "electronics", label: "Electronics" },
  { id: "furniture", label: "Furniture" },
  { id: "pet_shop", label: "Pet Shop" },
  { id: "auto_parts", label: "Auto Parts" },
  { id: "sports", label: "Sports Shop" },
  { id: "coffee", label: "Coffee Store" },
  { id: "jewelry", label: "Jewelry" },
  { id: "handmade", label: "Handmade" },
];
