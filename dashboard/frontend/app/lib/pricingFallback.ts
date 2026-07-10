import type { PricingDisplay } from "./pricingApi";

/** Mission 1 truth catalog — keep in sync with backend public_truth_catalog.py */
export const PUBLIC_LANDING_MIN_EUR = 350;

const UNIVERSAL_PATH =
  "Диалог → концепция → совместная работа → согласование → разовая покупка или подписка";

/** Offline fallback when /api/public/pricing is unreachable. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "mission1-truth-7-fallback",
  disclaimer: {
    ru: `**Любая услуга** Virtus Core: ${UNIVERSAL_PATH}. Ориентировочные цены сразу в валюте целевого рынка. Сайт на /order от ${PUBLIC_LANDING_MIN_EUR} € (DE checkout).`,
  },
  platform_status: {
    label: "Virtus Studio — подписка, в разработке",
    body: "Подписка — цифровая компания с Vector, не скидка на услугу. Сейчас: Vector Free и разовые услуги.",
  },
  service_vs_product: {
    ru: "**Разовая покупка** = готовый результат и передача. **Подписка** = проект остаётся в Virtus Core.",
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
      name: "Vector Free",
      price_eur_month: 0,
      price_label: "0 €",
      period: "/мес",
      audience: "Познакомиться с цифровой компанией",
      tagline: "Работа с Vector без оплаты",
      features: ["Консультация", "Первые шаги", "Проекты в компании"],
      cta: "Начать работу",
      cta_href: "/site",
      available: true,
    },
    {
      id: "pro",
      name: "Vector Pro",
      price_label: "скоро",
      period: "/мес",
      audience: "Предприниматели",
      tagline: "Цифровая компания — не скидка на услугу",
      features: ["Проекты в Virtus Core", "Развитие сайтов и документов"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
    {
      id: "team",
      name: "Vector Team",
      price_label: "скоро",
      period: "/мес",
      audience: "Команда и проекты",
      tagline: "Совместная цифровая компания",
      features: ["Команда", "Цифровые сотрудники"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
    {
      id: "enterprise",
      name: "Vector Enterprise",
      price_label: "скоро",
      period: "/мес",
      audience: "Масштаб и интеграции",
      tagline: "Корпоративная платформа",
      features: ["Enterprise", "Интеграции"],
      cta: "Скоро",
      cta_href: "/products",
      available: false,
    },
  ],
  services: [],
  business_units: [],
};
