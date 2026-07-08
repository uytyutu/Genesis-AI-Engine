import type { PricingDisplay } from "./pricingApi";
import { STUDIO_NAME } from "./publicBrand";

/** Offline fallback — pages work even if backend is down. */
export const PRICING_FALLBACK: PricingDisplay = {
  version: "2.1-fallback",
  disclaimer: {
    ru: "Цены «от» — ориентир. Каталог загружен локально (API недоступен).",
  },
  capabilities: {
    headline: "Virtus Studio — инструменты",
    subheadline:
      "Подписка Studio — не «бесплатные сайты под ключ». Это инструменты, чтобы создавать проекты самостоятельно.",
    groups: [
      {
        title: "Studio Basic",
        items: ["Создание", "Редактирование", "Публикация", "До 2 проектов"],
      },
      {
        title: "Studio Pro",
        items: ["Больше проектов", "Автоматизация", "Команда", "Интеграции"],
      },
      {
        title: "Vector Chat",
        items: ["AI-консультант", "Память", "Голос", "Помощь 24/7"],
      },
    ],
    value_anchor:
      "Один сайт под ключ от 450 €. Studio выгоден, когда проектов много — вы платите за инструменты, не за нашу работу.",
  },
  service_vs_product: {
    headline: "Услуга или Studio?",
    service_when:
      "Нужен один готовый результат — сайт, бот, приложение. Virtus Core делает всё сам, под ключ.",
    product_when:
      "Планируете регулярно создавать проекты сами — Studio даёт инструменты (лимит проектов по тарифу). Это не замена услуги «под ключ».",
    cta_service: { label: "Каталог услуг", href: "/services" },
    cta_product: { label: "Virtus Studio", href: "/products#compare" },
  },
  anti_cannibalization: {
    headline: "Studio ≠ бесплатный сайт под ключ",
    body:
      "Подписка 49 €/мес не заменяет услугу за 450 €. Studio — платформа для самостоятельной работы с лимитом проектов. Один сайт — закажите услугу.",
    example_one_site:
      "Один лендинг → услуга от 450 €. Подписка сейчас не нужна — честно скажем об этом.",
  },
  service_categories: [
    {
      id: "websites",
      name: "Сайты под ключ",
      description: "Virtus Core делает сам — от идеи до публикации",
      items: [
        {
          id: "landing",
          name: "Landing Page",
          price_label: "от 450 €",
          timeline: "5–10 дней",
          includes: ["1 страница", "Адаптив", "Форма связи", "SEO-база"],
          description: "Готовый одностраничник — мы делаем, вы получаете результат",
          cta: "Заказать",
          cta_href: "/order",
          available: true,
        },
        {
          id: "corporate",
          name: "Корпоративный сайт",
          price_label: "от 850 €",
          timeline: "2–4 недели",
          includes: ["4–7 страниц", "CMS", "Контакты"],
          description: "Многостраничный сайт компании под ключ",
          cta: "Обсудить",
          cta_href: "mailto:hello@genesis-ai-engine.com?subject=Corporate%20Website",
          available: false,
        },
      ],
    },
    {
      id: "ai",
      name: "AI и боты",
      description: "Умные помощники — разработка и внедрение под ключ",
      items: [
        {
          id: "telegram_bot",
          name: "Telegram Bot",
          price_label: "от 250 €",
          timeline: "1–2 недели",
          includes: ["Сценарии", "Админка"],
          description: "Бот под ваш процесс",
          cta: "Обсудить",
          cta_href: "mailto:hello@genesis-ai-engine.com?subject=Telegram%20Bot",
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
      audience: "Попробовать Virtus Core",
      tagline: "Чат без карты",
      features: ["Базовый чат", "Ограниченные сообщения"],
      cta: "Начать на /site",
      cta_href: "/site",
      available: true,
    },
    {
      id: "basic",
      name: "Studio Basic",
      price_eur_month: 49,
      price_label: "49 €",
      period: "/мес",
      audience: "Делать проекты самому",
      tagline: "Инструменты · до 2 проектов",
      features: ["Создание", "Редактирование", "Публикация", "До 2 проектов", "Не включает работу под ключ"],
      cta: "Ранний доступ",
      cta_href: `mailto:hello@genesis-ai-engine.com?subject=${encodeURIComponent(STUDIO_NAME + " Basic")}`,
      available: false,
    },
    {
      id: "pro",
      name: "Studio Pro",
      price_eur_month: 99,
      price_label: "99 €",
      period: "/мес",
      audience: "Регулярные проекты",
      tagline: "Больше проектов · автоматизация",
      features: ["До 10 проектов", "Автоматизация", "Команда", "Marketing Lab"],
      cta: "Ранний доступ",
      cta_href: `mailto:hello@genesis-ai-engine.com?subject=${encodeURIComponent(STUDIO_NAME + " Pro")}`,
      highlight: true,
      available: false,
    },
  ],
  services: [],
  business_units: [],
  comparison: {
    columns: [
      { id: "free", label: "Free" },
      { id: "basic", label: "Basic" },
      { id: "pro", label: "Pro" },
    ],
    rows: [
      { feature: "Vector Chat", values: ["yes", "yes", "yes"] },
      { feature: "Studio: создать самому", values: ["no", "limited", "yes"] },
      { feature: "Сайт под ключ (мы делаем)", values: ["no", "no", "no"] },
    ],
  },
};
