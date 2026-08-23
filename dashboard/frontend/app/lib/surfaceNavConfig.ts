/**
 * M3.2 — Navigation config per surface (shell only, shared kernel).
 */

import { SURFACE_REGISTRY, type SurfaceTarget } from "./surfaceRegistry";

export type SurfaceNavMeta = {
  scenario: string;
  userFlow: string[];
};

const NAV = (SURFACE_REGISTRY as { navigation?: Record<string, unknown> }).navigation as
  | {
      unity_principle?: string;
      vector_center?: string;
      client_nav_paths?: string[];
      surfaces?: Record<SurfaceTarget, { scenario?: string; user_flow?: string[] }>;
    }
  | undefined;

export const NAV_UNITY = NAV?.unity_principle ?? "Один Virtus Core";
export const NAV_VECTOR_CENTER = NAV?.vector_center ?? "Работа с Vector";

export const CLIENT_NAV_PATHS: string[] = NAV?.client_nav_paths ?? [
  "/projects",
  "/client",
];

export function surfaceNavMeta(target: SurfaceTarget): SurfaceNavMeta {
  const s = NAV?.surfaces?.[target];
  return {
    scenario: s?.scenario ?? "",
    userFlow: s?.user_flow ?? [],
  };
}

export function resolveNavigationSurface(pathname: string): SurfaceTarget {
  if (
    pathname === "/owner-gate" ||
    pathname.startsWith("/owner-gate?")
  ) {
    return "public";
  }
  // Auth-only screens must never render Client Workspace chrome.
  if (
    pathname === "/client/login" ||
    pathname === "/client/register" ||
    pathname.startsWith("/client/login?") ||
    pathname.startsWith("/client/register?")
  ) {
    return "public";
  }
  if (
    pathname === "/client" ||
    pathname.startsWith("/client/") ||
    CLIENT_NAV_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))
  ) {
    return "client";
  }
  if (pathname === "/") return "ceo";
  if (pathname === "/engine" || pathname.startsWith("/engine/")) return "ceo";
  if (pathname === "/products") return "public";
  const mc = [
    "/finance",
    "/payout",
    "/farm-engine",
    "/income-engine",
    "/alpha-hunter",
    "/company",
    "/ai",
    "/cursor",
    "/revenue",
    "/marketplace",
    "/monitor",
    "/dev",
    "/check",
    "/create",
    "/settings",
    "/setup",
    "/launch",
    "/journal",
    "/business",
    "/opportunities",
    "/acquisition",
    "/support",
    "/clients",
    "/scanner",
    "/growth",
    "/tasks",
    "/tiktok-horizon",
    "/horizon",
    "/ceo-site",
    "/global-analytics",
    "/executive",
  ];
  if (mc.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return "ceo";
  }
  if (pathname === "/scanner" || pathname.startsWith("/scanner/")) {
    return "ceo";
  }
  return "public";
}

/** Purchase / intake paths — storefront look + quieter public chrome. */
export function isCustomerPurchasePath(pathname: string): boolean {
  const p = (pathname || "").split("?")[0] || "";
  return (
    p === "/order" ||
    p.startsWith("/order/") ||
    p === "/products" ||
    p.startsWith("/products/")
  );
}

export type PublicNavLink = {
  href: string;
  label: string;
  match: (p: string) => boolean;
};

export const PUBLIC_NAV_LINKS: readonly PublicNavLink[] = [];

export const CLIENT_NAV_LINKS = [
  { href: "/client", label: "Dashboard", hint: "Übersicht · Produkte · nächster Schritt" },
  { href: "/client/products", label: "Meine Produkte", hint: "Website · AI Store · Status" },
  { href: "/client/orders", label: "Bestellungen", hint: "Status · Download" },
  { href: "/client/shop", label: "Marketplace", hint: "Weitere Services bestellen" },
  {
    href: "/client/bots",
    label: "KI-Mitarbeiter",
    hint: "Setup · Kanäle · ehrlicher Status",
  },
  {
    href: "/client/billing",
    label: "Abrechnung",
    hint: "Zahlungsverlauf · Portal Soon",
  },
  {
    href: "/client/support",
    label: "Support",
    hint: "E-Mail · Tickets Soon",
  },
  {
    href: "/client/privacy",
    label: "Privacy",
    hint: "Cookies · Einwilligung",
  },
] as const;

export const CEO_PRIMARY_LINKS = [
  { href: "/executive", label: "CEO Dashboard", hint: "Утро · Virtus + Farm · Today Focus" },
  { href: "/business", label: "Бизнес", hint: "Mission 2 · KPI" },
  { href: "/acquisition", label: "Поиск лидов", hint: "Country Desk · все рынки · Path A" },
  { href: "/opportunities", label: "Возможности", hint: "Affiliate · Report · API · ROI сегодня" },
  { href: "/client/bots", label: "Боты", hint: "AI bots · цены по странам · отдельный продукт" },
  { href: "/support", label: "Поддержка", hint: "Inbox · автоответы · шаблоны" },
  { href: "/clients", label: "Клиенты", hint: "Business ID · Client Card · таймлайн" },
  { href: "/ceo-site", label: "Сайт клиентов", hint: "Превью /site + /order" },
  { href: "/", label: "Ферма", hint: "Разметка · Toloka Spend (не Desk)" },
  { href: "/farm-engine", label: "Farm Engine", hint: "Opire · Approve · Reward Protection" },
  {
    href: "/income-engine",
    label: "Alpha Hunter",
    hint: "Opportunity Discovery Engine · рынки · adapters · OWNER",
  },
  { href: "/journal", label: "Журнал", hint: "Доход · задачи" },
  { href: "/revenue", label: "Доход", hint: "Lab · Work Farm · ключи · API" },
  { href: "/payout", label: "Вывод", hint: "Payout Manager · REAL → банк" },
  { href: "/finance", label: "Финансы и налоги", hint: "Доходы · чеки · экспорт" },
] as const;

export const CEO_STUDIO_LINKS = [
  { href: "/cursor", label: "Разработка", hint: "Cursor · код" },
  { href: "/acquisition", label: "Country Desk", hint: "Все рынки · снайпер · Outbox" },
  { href: "/support", label: "Support", hint: "Inbox · Auto Rules · Templates" },
  { href: "/clients", label: "Clients", hint: "Business ID · Client Card · timeline" },
  { href: "/ceo-site", label: "Сайт клиентов", hint: "Как видит покупатель" },
  { href: "/tiktok-horizon", label: "TikTok Horizon", hint: "INTERNAL OWNER · OAuth · kill switch" },
  {
    href: "/horizon",
    label: "Horizon Studio",
    hint: "Media Engine · Creative Director · Internal Only",
  },
  { href: "/#lost-archive", label: "Архив отказов", hint: "lost_reasons · не удалять" },
  { href: "/create", label: "Фабрика", hint: "Сборка Landing" },
  { href: "/ai", label: "AI Hub", hint: "Помощник CEO" },
  { href: "/growth", label: "Аналитика", hint: "Mission 2 · Конверсия" },
] as const;

export const CEO_SYSTEM_LINKS = [
  { href: "/launch", label: "Запуск", hint: "Сервисы" },
  { href: "/check", label: "Разработчик", hint: "Диагностика" },
  { href: "/settings", label: "Настройки", hint: "Профиль" },
] as const;
