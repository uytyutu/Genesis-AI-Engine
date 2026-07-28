/**
 * G2.X — Commercial catalog (keep in sync with
 * dashboard/backend/app/integration/commercial_catalog_g23.py
 * and serviceOrderSpecs.ts).
 */

export type CommercialCategory = "one_time" | "monthly" | "product";
export type CommercialCta = "order_now" | "activate" | "coming_soon";

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
  group?: "websites" | "bots" | "website_services";
};

export const LANDING_PACKAGES_EUR = {
  basic: 350,
  business: 650,
  premium: 1200,
} as const;

/** Showcase sections for /products (G2.X). */
export const PRODUCT_SHOWCASE_GROUPS: {
  id: "websites" | "bots" | "website_services";
  title: string;
  blurb: string;
}[] = [
  {
    id: "websites",
    title: "Websites that bring leads",
    blurb: "Professional site for more customers — buy once, own the files.",
  },
  {
    id: "bots",
    title: "AI Digital Employee",
    blurb: "AI Sales Assistant for your company — one product, many channels.",
  },
  {
    id: "website_services",
    title: "Website Services",
    blurb: "Add-ons — order form first, then payment when the service is live.",
  },
];

export const COMMERCIAL_CATALOG: CommercialRow[] = [
  {
    id: "landing_website",
    category: "product",
    group: "websites",
    name: "Business Website That Brings Leads",
    price_label: `${LANDING_PACKAGES_EUR.basic}–${LANDING_PACKAGES_EUR.premium} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order",
    cta_label: "Order",
    includes: `Get more customers · Basic ${LANDING_PACKAGES_EUR.basic} € · Business ${LANDING_PACKAGES_EUR.business} € · Premium ${LANDING_PACKAGES_EUR.premium} €`,
  },
  {
    id: "ai_business_bot",
    category: "product",
    group: "bots",
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
  {
    id: "seo_audit",
    category: "one_time",
    group: "website_services",
    name: "SEO Audit",
    price_label: "249 €",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_href: "/order/service/seo_audit",
    cta_label: "Interest form",
    includes: "Technical + local SEO plan · form now, pay when live",
  },
  {
    id: "speed_optimization",
    category: "one_time",
    group: "website_services",
    name: "Speed Optimization",
    price_label: "199 €",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_href: "/order/service/speed_optimization",
    cta_label: "Interest form",
    includes: "Load-time improvements · form now, pay when live",
  },
  {
    id: "security_check",
    category: "one_time",
    group: "website_services",
    name: "Security Check",
    price_label: "299 €",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_href: "/order/service/security_check",
    cta_label: "Interest form",
    includes: "HTTPS, forms, vulnerability review · form now, pay when live",
  },
  {
    id: "google_business_setup",
    category: "one_time",
    group: "website_services",
    name: "Google Business Profile Setup",
    price_label: "149 €",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_href: "/order/service/google_business_setup",
    cta_label: "Interest form",
    includes: "Intake form ready · checkout when delivery is live",
  },
  {
    id: "website_migration",
    category: "one_time",
    group: "website_services",
    name: "Website Migration",
    price_label: "from 299 €",
    billing: "one_time",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_href: "/order/service/website_migration",
    cta_label: "Interest form",
    includes: "Move site to new hosting · form now, pay when live",
  },
];
