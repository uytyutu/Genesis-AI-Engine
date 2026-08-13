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
  brandLine: "Virtus AI Workspace",
  themePrefs: "Design / Modus",
  modePreview: "Workspace-Modus (Vorschau)",
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
    backup: "Sicherung",
    domain: "Domain",
    stats_basic: "Statistik",
    marketplace: "Business erweitern",
    ai_assistant: "Virtus AI",
    bots: "KI-Mitarbeiter",
    billing: "Abrechnung",
    support: "Support",
    downloads: "Downloads",
  },
};

const EN: Copy = {
  brandLine: "Virtus AI Workspace",
  themePrefs: "Theme / mode",
  modePreview: "Workspace mode (preview)",
  standalone: "Standalone",
  connected: "Connected",
  language: "Language",
  nav: {
    dashboard: "Dashboard",
    site: "Website",
    pages: "Pages",
    media: "Media",
    texts: "Texts",
    contacts: "Contacts",
    products: "My products",
    orders: "Orders",
    settings: "Settings",
    backup: "Backup",
    domain: "Domain",
    stats_basic: "Stats",
    marketplace: "Grow your business",
    ai_assistant: "Virtus AI",
    bots: "AI Employee",
    billing: "Billing",
    support: "Support",
    downloads: "Downloads",
  },
};

const RU: Copy = {
  brandLine: "Virtus AI Workspace",
  themePrefs: "Тема / режим",
  modePreview: "Режим Workspace (превью)",
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
    backup: "Резервная копия",
    domain: "Домен",
    stats_basic: "Статистика",
    marketplace: "Расширьте бизнес",
    ai_assistant: "Virtus AI",
    bots: "AI-сотрудник",
    billing: "Оплата",
    support: "Поддержка",
    downloads: "Загрузки",
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
