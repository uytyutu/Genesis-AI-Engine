import type { PricingDisplay } from "./pricingApi";

/** Mission 1 truth catalog — keep in sync with backend public_truth_catalog.py */
export const PUBLIC_LANDING_MIN_EUR = 350;

const UNIVERSAL_PATH =
  "Диалог → концепция → совместная работа → согласование → разовая покупка или подписка";

/** Offline fallback when /api/public/pricing is unreachable. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "mission1-truth-12-fallback",
  disclaimer: {
    ru: `**Любая услуга** Virtus Core: ${UNIVERSAL_PATH}. Ориентировочные цены сразу в валюте целевого рынка. Сайт на /order от ${PUBLIC_LANDING_MIN_EUR} € (DE checkout).`,
  },
  platform_status: {
    label: "Virtus Studio — подписка, в разработке",
    body: "Подписка — этап роста цифровой компании с Vector. Сейчас: Free (без срока) и разовые услуги.",
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
    {
      id: "document_analysis",
      name: "Анализ документов",
      description: "Тот же путь: диалог → концепция → согласование → выбор.",
      items: [
        {
          id: "document_analysis",
          name: "Document Analysis",
          price_label: "по запросу",
          timeline: "—",
          includes: [],
          description: "Доступно в диалоге с Vector",
          cta: "Обсудить с Vector",
          cta_href: "/site",
          available: true,
        },
      ],
    },
    {
      id: "business_plan",
      name: "Бизнес-план",
      description: "Скоро — тот же универсальный сценарий.",
      items: [
        {
          id: "business_plan",
          name: "Business Plan",
          price_label: "скоро",
          timeline: "—",
          includes: [],
          description: UNIVERSAL_PATH,
          cta: "Скоро",
          cta_href: "/site",
          available: false,
        },
      ],
    },
    {
      id: "automation",
      name: "Автоматизация",
      description: "Скоро — тот же универсальный сценарий.",
      items: [
        {
          id: "automation",
          name: "Automation",
          price_label: "скоро",
          timeline: "—",
          includes: [],
          description: UNIVERSAL_PATH,
          cta: "Скоро",
          cta_href: "/site",
          available: false,
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
      name: "Professional",
      price_eur_month: null,
      price_label: "скоро",
      period: "/мес",
      audience: "Начало работы",
      tagline: "Начало работы с цифровой компанией",
      features: ["Несколько проектов", "Голосовой Vector", "Развитие результатов"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
    {
      id: "business",
      name: "Business",
      price_eur_month: null,
      price_label: "скоро",
      period: "/мес",
      audience: "Рост компании",
      tagline: "Рост цифровой компании",
      features: ["CRM", "Автоматизация", "Маркетинг", "Совместная работа"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price_eur_month: null,
      price_label: "скоро",
      period: "/мес",
      audience: "Масштабирование",
      tagline: "Масштабирование цифровой компании",
      features: ["Команда", "Роли", "Интеграции", "Приоритетная поддержка"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
  ],
  services: [],
  business_units: [],
};
