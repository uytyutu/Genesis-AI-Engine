/**
 * G2.X — Commercial catalog (keep in sync with
 * dashboard/backend/app/integration/commercial_catalog_g23.py).
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
    title: "Websites",
    blurb: "Landing packages — buy once, own the files.",
  },
  {
    id: "bots",
    title: "AI Business Bot",
    blurb: "Digital employees for your company — one product, many channels.",
  },
  {
    id: "website_services",
    title: "Website Services",
    blurb: "Add-ons for any site — yours or one we built.",
  },
];

export const COMMERCIAL_CATALOG: CommercialRow[] = [
  {
    id: "landing_website",
    category: "product",
    group: "websites",
    name: "Landing Websites",
    price_label: `${LANDING_PACKAGES_EUR.basic}–${LANDING_PACKAGES_EUR.premium} €`,
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order",
    cta_label: "Order",
    includes: `Basic ${LANDING_PACKAGES_EUR.basic} € · Business ${LANDING_PACKAGES_EUR.business} € · Premium ${LANDING_PACKAGES_EUR.premium} €`,
  },
  {
    id: "ai_business_bot",
    category: "product",
    group: "bots",
    name: "AI Business Bot",
    price_label: "499–1499 € setup + 99–349 €/mo",
    billing: "monthly",
    availability: "available",
    cta: "order_now",
    cta_href: "/order/bot?package=bot_business",
    cta_label: "Order",
    includes:
      "1 / up to 3 / Fair Use AI-bots · Website Chat · Telegram · WhatsApp · Instagram · Messenger",
  },
  {
    id: "ai_website_analysis",
    category: "one_time",
    group: "website_services",
    name: "AI Website Analysis",
    price_label: "149 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=ai_website_analysis",
    cta_label: "Order",
    includes: "Report + priorities · no website purchase required",
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
    cta_href: "/order?package=website_repair",
    cta_label: "Order",
    includes: "Repair existing site · sold separately from Landing",
  },
  {
    id: "seo_audit",
    category: "one_time",
    group: "website_services",
    name: "SEO Audit",
    price_label: "249 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=seo_audit",
    cta_label: "Order",
    includes: "Technical + local SEO plan · standalone",
  },
  {
    id: "speed_optimization",
    category: "one_time",
    group: "website_services",
    name: "Speed Optimization",
    price_label: "199 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=speed_optimization",
    cta_label: "Order",
    includes: "Load-time improvements · standalone",
  },
  {
    id: "security_check",
    category: "one_time",
    group: "website_services",
    name: "Security Check",
    price_label: "299 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=security_check",
    cta_label: "Order",
    includes: "HTTPS, forms, vulnerability review · standalone",
  },
  {
    id: "google_business_setup",
    category: "one_time",
    group: "website_services",
    name: "Google Business Profile Setup",
    price_label: "149 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=google_business_setup",
    cta_label: "Order",
    includes: "Profile setup for local discovery · standalone",
  },
  {
    id: "website_migration",
    category: "one_time",
    group: "website_services",
    name: "Website Migration",
    price_label: "from 299 €",
    billing: "one_time",
    availability: "available",
    cta: "order_now",
    cta_href: "/order?package=website_migration",
    cta_label: "Order",
    includes: "Move site to new hosting · standalone",
  },
  // Monthly modules still priced, not sold as unfinished CRM/automation
  {
    id: "crm_starter",
    category: "monthly",
    name: "CRM Starter",
    price_label: "29 €/mo",
    billing: "monthly",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_label: "Coming Soon",
    includes: "Contacts · pipeline basics",
  },
  {
    id: "automation_starter",
    category: "monthly",
    name: "Automation Starter",
    price_label: "49 €/mo",
    billing: "monthly",
    availability: "coming_soon",
    cta: "coming_soon",
    cta_label: "Coming Soon",
    includes: "Simple workflows",
  },
];
