/**
 * Commercial catalog — Digital Business Creator.
 * Keep in sync with dashboard/backend/app/factory/solution_catalog.py
 * and commercial_catalog_g23.py.
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

/** Standalone vs Connected — not Basic / Business / Premium. */
export const LANDING_PACKAGES_EUR = {
  standalone: 499,
  connected: 499,
  connected_monthly: 99,
  // Legacy aliases (API / unpaid demos)
  basic: 499,
  business: 499,
  premium: 499,
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
    id: "digital_business_standalone",
    category: "product",
    group: "websites",
    name: "Standalone — own your digital product",
    price_label: `${LANDING_PACKAGES_EUR.standalone} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=standalone",
    cta_label: "Get Standalone",
    includes:
      "Full digital company site · panel · source · Business Interview → brand → site",
  },
  {
    id: "digital_business_connected",
    category: "product",
    group: "websites",
    name: "Virtus Core Connected",
    price_label: `${LANDING_PACKAGES_EUR.connected} € + ${LANDING_PACKAGES_EUR.connected_monthly} €/mo`,
    billing: "monthly",
    availability: "available",
    cta: "activate",
    cta_href: "/order?package=connected",
    cta_label: "Connect to Virtus Core",
    includes:
      "Everything in Standalone + Workspace, CRM/leads, AI, automation, platform updates",
  },
  {
    id: "ai_store",
    category: "product",
    group: "stores",
    name: "AI Online Store",
    price_label: "from 799 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/shop",
    cta_label: "Order store",
    includes: "Industry store · catalog · checkout · panel",
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
      "AI Sales Assistant · Website Chat · Telegram · WhatsApp · Instagram · Messenger",
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
