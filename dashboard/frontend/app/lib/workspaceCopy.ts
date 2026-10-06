/** Client Workspace chrome copy — DE / EN / RU (market-first DE). */

export type WorkspaceUiLang = "de" | "en" | "ru";

type Copy = {
  brandLine: string;
  themePrefs: string;
  modePreview: string;
  standalone: string;
  connected: string;
  language: string;
  nav: Record<string, string>;
};

const DE: Copy = {
  brandLine: "Persönliches Konto",
  themePrefs: "Sprache",
  modePreview: "Konto",
  standalone: "Standalone",
  connected: "Connected",
  language: "Sprache",
  nav: {
    dashboard: "Übersicht",
    site: "Website",
    pages: "Seiten",
    media: "Medien",
    texts: "Texte",
    contacts: "Kontakte",
    products: "Meine Produkte",
    orders: "Bestellungen",
    settings: "Einstellungen",
    backup: "Dateien",
    domain: "Domain",
    stats_basic: "Statistik",
    marketplace: "Business erweitern",
    ai_assistant: "Virtus AI",
    chatbots: "KI-Mitarbeiter",
    bots: "KI-Mitarbeiter",
    inbox: "Posteingang",
    billing: "Zahlungen",
    support: "Hilfe",
    crm: "CRM",
    analytics: "Analytics",
    automations: "Automation",
    email_marketing: "E-Mail-Marketing",
    whatsapp: "WhatsApp",
    booking: "Buchung",
    notifications: "Benachrichtigungen",
    campaign_studio: "AI Campaign Studio",
    downloads: "Dateien",
  },
};

const EN: Copy = {
  brandLine: "Personal account",
  themePrefs: "Language",
  modePreview: "Account",
  standalone: "Standalone",
  connected: "Connected",
  language: "Language",
  nav: {
    dashboard: "Overview",
    site: "Website",
    pages: "Pages",
    media: "Media",
    texts: "Texts",
    contacts: "Contacts",
    products: "My products",
    orders: "Orders",
    settings: "Settings",
    backup: "Files",
    domain: "Domain",
    stats_basic: "Stats",
    marketplace: "Grow your business",
    ai_assistant: "Virtus AI",
    bots: "AI Employee",
    chatbots: "AI Employee",
    inbox: "Inbox",
    billing: "Payments",
    support: "Help",
    downloads: "Files",
  },
};

const RU: Copy = {
  brandLine: "Личный кабинет",
  themePrefs: "Язык",
  modePreview: "Кабинет",
  standalone: "Standalone",
  connected: "Connected",
  language: "Язык",
  nav: {
    dashboard: "Обзор",
    site: "Сайт",
    pages: "Страницы",
    media: "Медиа",
    texts: "Тексты",
    contacts: "Контакты",
    products: "Мои продукты",
    orders: "Заказы",
    settings: "Настройки",
    backup: "Файлы",
    domain: "Домен",
    stats_basic: "Статистика",
    marketplace: "Расширить бизнес",
    ai_assistant: "Virtus AI",
    bots: "AI-сотрудник",
    chatbots: "AI-сотрудник",
    inbox: "Входящие",
    billing: "Оплата",
    support: "Помощь",
    downloads: "Файлы",
  },
};

const MAP: Record<WorkspaceUiLang, Copy> = { de: DE, en: EN, ru: RU };

export function workspaceUiLang(code: string | undefined | null): WorkspaceUiLang {
  const c = (code || "de").slice(0, 2).toLowerCase();
  if (c === "en" || c === "ru") return c;
  return "de";
}

export function workspaceCopy(lang: WorkspaceUiLang): Copy {
  return MAP[lang] || DE;
}
