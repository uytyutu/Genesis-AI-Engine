import type { PricingDisplay } from "./pricingApi";

/** Mission 1 truth catalog — keep in sync with backend public_truth_catalog.py / sales_order_service packages. */
export const PUBLIC_LANDING_MIN_EUR = 350;

/** Offline fallback when /api/public/pricing is unreachable. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "mission1-truth-1-fallback",
  disclaimer: {
    ru: `Сейчас онлайн можно заказать лендинг (${PUBLIC_LANDING_MIN_EUR}–1200 €). Virtus Studio пока нельзя купить — только разговор на /site и заказ на /order.`,
  },
  platform_status: {
    label: "Virtus Studio — в разработке",
    body: "Подписка Virtus Studio пока недоступна. Сейчас: Vector на /site и заказ лендинга на /order.",
  },
  service_categories: [
    {
      id: "landing",
      name: "Лендинг под ключ",
      description:
        "Обсудите задачу с Vector на /site — затем оформите заказ. Пакеты совпадают с /order (350 / 650 / 1200 €).",
      items: [
        {
          id: "landing",
          name: "Landing Page",
          price_label: `от ${PUBLIC_LANDING_MIN_EUR} €`,
          timeline: "5–14 дней",
          includes: ["1 страница", "Адаптив", "Контакты", "SEO-база"],
          description: "Одностраничный сайт — финальная цена на шаге заказа",
          cta: "Заказать",
          cta_href: "/order",
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
      period: "/мес",
      audience: "Познакомиться с Vector",
      tagline: "Чат на /site",
      features: ["Разговор с Vector", "Обсуждение идеи", "Ориентир по цене лендинга"],
      cta: "Начать на /site",
      cta_href: "/site",
      available: true,
    },
  ],
  services: [],
  business_units: [],
};
