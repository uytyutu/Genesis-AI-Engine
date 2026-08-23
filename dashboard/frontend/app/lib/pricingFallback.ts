import type { PricingDisplay } from "./pricingApi";

/** Mission 1 truth catalog — keep in sync with backend pricing_engine /site ladder */
export const PUBLIC_LANDING_MIN_EUR = 299;

const UNIVERSAL_PATH_DE =
  "Dialog → Konzept → Zusammenarbeit → Freigabe → Einmalkauf oder Abo";

/** Offline fallback when /api/public/pricing is unreachable. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "g23-commercial-1-fallback",
  disclaimer: {
    de: `**Jede Leistung** von Virtus Core: ${UNIVERSAL_PATH_DE}. Richtpreise in der Währung des Zielmarkts. Website auf /order ab ${PUBLIC_LANDING_MIN_EUR} € (DE-Checkout).`,
    ru: `**Любая услуга** Virtus Core: Диалог → концепция → совместная работа → согласование → разовая покупка или подписка. Ориентировочные цены сразу в валюте целевого рынка. Сайт на /order от ${PUBLIC_LANDING_MIN_EUR} € (DE checkout).`,
    en: `**Any Virtus Core service:** Dialog → concept → co-creation → approval → one-time purchase or subscription. Guide prices in the target market currency. Website on /order from ${PUBLIC_LANDING_MIN_EUR} € (DE checkout).`,
  },
  platform_status: {
    label: "Virtus Studio — Abo, demnächst",
    body: "Vector monatlich Starter 99 € · Business 199 € · Professional 349 € / Mon. (Checkout demnächst). Jetzt: Free und Website-Bestellung.",
  },
  service_vs_product: {
    headline: "Leistung oder Abo",
    service_when: "Einmalkauf — fertiges Ergebnis und Projektübergabe.",
    product_when: "Abo — das Projekt bleibt in Virtus Core, Vector arbeitet weiter.",
    cta_service: { label: "Bestellen", href: "/order" },
    cta_product: { label: "Vector", href: "/site" },
  },
  service_categories: [
    {
      id: "website",
      name: "Website für Ihr Unternehmen",
      description:
        "Einmalige Leistung — fertige Website. Vector begleitet bis zur Freigabe; nach Zahlung — Projektübergabe.",
      items: [
        {
          id: "basic",
          name: "Website Basic",
          price_label: "299 €",
          timeline: "5–14 Tage",
          includes: [
            "Moderne responsive Website",
            "Bis zu 5 Seiten",
            "Kontaktformular",
            "Impressum · Datenschutz",
            "Ohne Admin-Panel",
          ],
          description: "Für den Start — moderne Website ohne Admin-Panel",
          cta: "Jetzt bestellen",
          cta_href: "/order?package=basic",
          available: true,
        },
        {
          id: "business",
          name: "Website Business",
          price_label: "599 €",
          timeline: "5–14 Tage",
          includes: [
            "Alles aus Basic",
            "Website Admin Dashboard",
            "Blog",
            "Analytics",
            "Content-Verwaltung",
          ],
          description: "Alles aus Basic — plus Admin Dashboard, Blog und Content",
          cta: "Jetzt bestellen",
          cta_href: "/order?package=business",
          available: true,
        },
        {
          id: "premium",
          name: "Website Premium",
          price_label: "999 €",
          timeline: "5–14 Tage",
          includes: [
            "Alles aus Business",
            "Benutzerrollen",
            "SEO Pro",
            "AI Vector in der Panel",
            "Priorisierter Support",
          ],
          description: "Fast Corporate: Rollen, SEO Pro, AI Vector",
          cta: "Jetzt bestellen",
          cta_href: "/order?package=premium",
          available: true,
        },
      ],
    },
  ],
  subscriptions: [
    {
      id: "free",
      name: "Free",
      price_eur_month: 0,
      price_label: "0 €",
      period: "/Mon.",
      audience: "Kennenlernen",
      tagline: "Kennenlernen der digitalen Firma",
      features: ["Ohne Laufzeit", "Ein aktives Projekt", "Begrenzte Nachrichten"],
      cta: "Loslegen",
      cta_href: "/site",
      available: true,
    },
    {
      id: "core",
      name: "Vector Starter",
      price_eur_month: 99,
      price_label: "99 €",
      period: "/Mon.",
      audience: "AI Business Employee",
      tagline: "Website-Widget · begrenzte Gespräche",
      features: ["Setup ab 499 €", "Checkout demnächst"],
      cta: "Demnächst",
      cta_href: "/products",
      available: false,
    },
    {
      id: "business",
      name: "Vector Business",
      price_eur_month: 199,
      price_label: "199 €",
      period: "/Mon.",
      audience: "AI Business Employee",
      tagline: "Mehr Volumen · Kanäle",
      features: ["Checkout demnächst"],
      cta: "Demnächst",
      cta_href: "/products",
      available: false,
    },
    {
      id: "enterprise",
      name: "Vector Professional",
      price_eur_month: 349,
      price_label: "349 €",
      period: "/Mon.",
      audience: "AI Business Employee",
      tagline: "Priorität · Integrationen",
      features: ["Checkout demnächst"],
      cta: "Demnächst",
      cta_href: "/products",
      available: false,
    },
  ],
  services: [],
  business_units: [],
};
