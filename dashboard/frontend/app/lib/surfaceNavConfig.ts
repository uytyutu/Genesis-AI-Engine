/**
 * M3.2 — Navigation config per surface (shell only, shared kernel).
 */

import { isClientTradingPath } from "./clientTradingRoutes";
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
  // Client paper vitrine — never Mission Control chrome.
  if (isClientTradingPath(pathname)) return "public";
  const mc = [
    "/finance",
    "/money",
    "/payout",
    "/affiliate",
    "/trade",
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
  { href: "/client", label: "Übersicht", hint: "Produkte · nächster Schritt" },
  { href: "/client/products", label: "Meine Produkte", hint: "Website · Shop · Status" },
  { href: "/client/orders", label: "Bestellungen", hint: "Status · Dateien" },
  { href: "/client/shop", label: "Business erweitern", hint: "Website · Shop · AI" },
  {
    href: "/client/bots",
    label: "KI-Mitarbeiter",
    hint: "Setup · Kanäle",
  },
  {
    href: "/client/billing",
    label: "Zahlungen",
    hint: "Zahlungsverlauf",
  },
  {
    href: "/client/support",
    label: "Hilfe",
    hint: "Support · Kontakt",
  },
] as const;

export const MC_NAV_SECTIONS = [
  {
    title: "OVERVIEW",
    items: [{ href: "/executive", label: "Обзор", hint: "Деньги · клиенты · сегодня" }],
  },
  {
    title: "BUSINESS",
    items: [
      { href: "/executive/marketing", label: "AI Маркетинг", hint: "Research · Ideas · Approve" },
      { href: "/executive/sales", label: "Продажи", hint: "Выручка · чек · повтор" },
      { href: "/executive/orders", label: "Заказы", hint: "Paid · pending · refund" },
      { href: "/executive/customers", label: "Клиенты", hint: "CRM · Virtus ID" },
      { href: "/executive/payments", label: "Оплаты", hint: "Stripe · статус" },
      { href: "/executive/analytics", label: "Аналитика", hint: "Воронка · конверсия" },
    ],
  },
  {
    title: "PRODUCTS",
    items: [
      { href: "/executive/products/websites", label: "Сайты", hint: "Factory · demos" },
      { href: "/executive/products/stores", label: "Интернет-магазины", hint: "AI Store" },
      { href: "/executive/products/bots", label: "AI-Боты", hint: "AI Employee" },
      { href: "/executive/oracle", label: "Virtus Oracle", hint: "Пользователи · монеты · расклады" },
    ],
  },
  {
    title: "COMMUNICATION",
    items: [
      { href: "/executive/messages", label: "Сообщения", hint: "Каналы · ответ" },
      { href: "/executive/leads", label: "Заявки", hint: "Новые лиды" },
      { href: "/executive/support", label: "Поддержка", hint: "Входящие письма" },
    ],
  },
  {
    title: "OPERATIONS",
    items: [
      { href: "/executive/operations", label: "Factory", hint: "Сборки · ZIP · gates" },
      { href: "/create", label: "Deployments", hint: "Публикация" },
      { href: "/executive/system", label: "System", hint: "Здоровье сервисов" },
    ],
  },
  {
    title: "SETTINGS",
    items: [{ href: "/settings", label: "Настройки", hint: "Профиль" }],
  },
] as const;

export const MC_PULT_LINKS = [
  { href: "/executive", label: "Обзор", hint: "Деньги · клиенты · сегодня" },
  { href: "/executive/sales", label: "Продажи", hint: "Выручка" },
  { href: "/executive/customers", label: "Клиенты", hint: "CRM" },
  { href: "/executive/oracle", label: "Oracle", hint: "Эфир" },
  { href: "/executive/marketing", label: "AI Маркетинг", hint: "Owner AI" },
  { href: "/executive/operations", label: "Операции", hint: "Factory · gates" },
] as const;

export const CEO_PRIMARY_LINKS = MC_PULT_LINKS;

export const CEO_STUDIO_LINKS = [
  { href: "/executive/products/websites", label: "Сайты", hint: "Factory" },
  { href: "/executive/products/stores", label: "Магазины", hint: "AI Store" },
  { href: "/executive/products/bots", label: "Боты", hint: "AI-сотрудники" },
  { href: "/executive/oracle", label: "Oracle", hint: "Эфир" },
  { href: "/executive/customers", label: "Клиенты", hint: "Карточки" },
] as const;

export const CEO_SYSTEM_LINKS = [
  { href: "/settings", label: "Настройки", hint: "Профиль" },
] as const;
