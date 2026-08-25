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
    "/farm",
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
    "/factory",
    "/orders",
    "/settings",
    "/setup",
    "/launch",
    "/journal",
    "/business",
    "/opportunities",
    "/acquisition",
    "/support",
    "/clients",
    "/users",
    "/scanner",
    "/growth",
    "/tasks",
    "/tiktok-horizon",
    "/horizon",
    "/ceo-site",
    "/global-analytics",
    "/executive",
    "/executive-legacy",
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

/** BCC sidebar — single chrome with ClientMobileNav (no duplicate shell chips). */
export const CLIENT_NAV_LINKS = [
  { href: "/client", label: "Übersicht", hint: "Ihr Kabinett" },
  { href: "/client/products", label: "Meine Produkte", hint: "Website · Shop · Status" },
  { href: "/client/site", label: "Website", hint: "Preview · Admin" },
  { href: "/client/shop", label: "Shop", hint: "Store Admin · Marketplace" },
  { href: "/client/bots", label: "AI", hint: "KI-Mitarbeiter · Inbox" },
  { href: "/client/settings", label: "Business", hint: "Profil · Branding · Coming Soon" },
  { href: "/client/billing", label: "Abrechnung", hint: "Zahlungsverlauf · Portal Demnächst" },
  { href: "/client/support", label: "Support", hint: "E-Mail · Tickets Demnächst" },
] as const;

/** MC 2.0 primary — только коммерческий Virtus (без Farm). Язык оболочки: RU. */
export const CEO_PRIMARY_LINKS = [
  { href: "/executive", label: "Обзор", hint: "Клиенты · заказы · выручка" },
  { href: "/users", label: "Пользователи", hint: "Список · карточка · заказы" },
  { href: "/orders", label: "Заказы", hint: "Оплата · Factory · ZIP" },
  { href: "/factory", label: "Продукты", hint: "Website · Shop · AI" },
  { href: "/acquisition", label: "Продажи", hint: "Country Desk · лиды" },
  { href: "/support", label: "Поддержка", hint: "Обращения · ответы" },
  { href: "/finance", label: "Финансы", hint: "Реальная выручка" },
  { href: "/ai", label: "Vector", hint: "AI для владельца" },
] as const;

/** Studios / Labs — свёрнуты, не ежедневный путь. */
export const CEO_STUDIO_LINKS = [
  { href: "/farm", label: "Ферма", hint: "Архив · Toloka · разметка" },
  { href: "/farm-engine", label: "Farm Engine", hint: "Архив · Opire" },
  { href: "/income-engine", label: "Alpha Hunter", hint: "Архив · lab" },
  { href: "/revenue", label: "Revenue Lab", hint: "Архив" },
  { href: "/payout", label: "Вывод Farm", hint: "Архив · не Stripe" },
  { href: "/opportunities", label: "Earn Marketplace", hint: "Архив" },
  { href: "/journal", label: "Журнал Farm", hint: "Архив" },
  { href: "/tiktok-horizon", label: "TikTok", hint: "Студия" },
  { href: "/horizon", label: "Horizon", hint: "Студия" },
  { href: "/create", label: "Factory Wizard", hint: "Сборка" },
  { href: "/executive-legacy", label: "Старый CEO Dashboard", hint: "Архив экрана" },
  { href: "/ceo-site", label: "Публичный сайт", hint: "/site · /order" },
  { href: "/cursor", label: "Разработка", hint: "Cursor" },
  { href: "/business", label: "Business Health", hint: "Mission 2" },
  { href: "/growth", label: "Аналитика M2", hint: "Конверсия" },
] as const;

export const CEO_SYSTEM_LINKS = [
  { href: "/launch", label: "Запуск", hint: "Checklist" },
  { href: "/check", label: "Здоровье", hint: "System check" },
  { href: "/monitor", label: "Монитор", hint: "Модули" },
  { href: "/settings", label: "Настройки", hint: "Профиль" },
] as const;
