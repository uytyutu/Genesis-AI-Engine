import type { PricingDisplay } from "./pricingApi";

/** Mission 1 truth catalog — keep in sync with backend public_truth_catalog.py */
export const PUBLIC_LANDING_MIN_EUR = 350;

const UNIVERSAL_PATH =
  "Диалог → концепция → совместная работа → согласование → разовая покупка или подписка";

/** Offline fallback when /api/public/pricing is unreachable. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "g23-commercial-1-fallback",
  disclaimer: {
    ru: `**Любая услуга** Virtus Core: ${UNIVERSAL_PATH}. Ориентировочные цены сразу в валюте целевого рынка. Сайт на /order от ${PUBLIC_LANDING_MIN_EUR} € (DE checkout).`,
  },
  platform_status: {
    label: "Virtus Studio — подписка, Coming Soon",
    body: "Vector monthly Starter 99 € · Business 199 € · Professional 349 € / mo (checkout Coming Soon). Сейчас: Free и заказ лендинга.",
  },
  service_vs_product: {
    headline: "Услуга или подписка",
    service_when: "Разовая покупка — готовый результат и передача проекта.",
    product_when: "Подписка — проект остаётся в Virtus Core, Vector продолжает работать.",
    cta_service: { label: "Оформить заказ", href: "/order" },
    cta_product: { label: "Vector", href: "/site" },
  },
  service_categories: [
    {
      id: "website",
      name: "Сайт для бизнеса",
      description:
        "Разовая услуга — готовый сайт. Vector ведёт до утверждения; после оплаты — передача проекта.",
      items: [
        {
          id: "basic",
          name: "Business Website",
          price_label: "350 €",
          timeline: "5–14 дней",
          includes: ["1 страница", "Адаптив", "Контакты", "SEO-база"],
          description: "Сайт под ключ — не подписка",
          cta: "Обсудить с Vector",
          cta_href: "/site",
          available: true,
        },
        {
          id: "business",
          name: "Professional Website",
          price_label: "650 €",
          timeline: "5–14 дней",
          includes: ["Расширенный лендинг", "Логотип в макете", "Формы", "SEO"],
          description: "Сайт под ключ — не подписка",
          cta: "Обсудить с Vector",
          cta_href: "/site",
          available: true,
        },
        {
          id: "premium",
          name: "Premium Business Website",
          price_label: "1200 €",
          timeline: "5–14 дней",
          includes: ["Премиум дизайн", "Домен", "Расширенное SEO", "Поддержка"],
          description: "Сайт под ключ — не подписка",
          cta: "Обсудить с Vector",
          cta_href: "/site",
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
      audience: "Знакомство",
      tagline: "Знакомство с цифровой компанией",
      features: ["Без срока", "Один активный проект", "Ограниченные сообщения"],
      cta: "Начать работу",
      cta_href: "/site",
      available: true,
    },
    {
      id: "core",
      name: "Vector Starter",
      price_eur_month: 99,
      price_label: "99 €",
      period: "/мес",
      audience: "AI Business Employee",
      tagline: "Website widget · limited conversations",
      features: ["Setup from 499 €", "Checkout Coming Soon"],
      cta: "Coming Soon",
      cta_href: "/products",
      available: false,
    },
    {
      id: "business",
      name: "Vector Business",
      price_eur_month: 199,
      price_label: "199 €",
      period: "/мес",
      audience: "AI Business Employee",
      tagline: "More volume · channels",
      features: ["Checkout Coming Soon"],
      cta: "Coming Soon",
      cta_href: "/products",
      available: false,
    },
    {
      id: "enterprise",
      name: "Vector Professional",
      price_eur_month: 349,
      price_label: "349 €",
      period: "/мес",
      audience: "AI Business Employee",
      tagline: "Priority · integrations",
      features: ["Checkout Coming Soon"],
      cta: "Coming Soon",
      cta_href: "/products",
      available: false,
    },
  ],
  services: [],
  business_units: [],
};
