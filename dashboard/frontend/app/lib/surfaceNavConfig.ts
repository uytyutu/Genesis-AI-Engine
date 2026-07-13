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

export const CLIENT_NAV_PATHS: string[] = NAV?.client_nav_paths ?? ["/projects"];

export function surfaceNavMeta(target: SurfaceTarget): SurfaceNavMeta {
  const s = NAV?.surfaces?.[target];
  return {
    scenario: s?.scenario ?? "",
    userFlow: s?.user_flow ?? [],
  };
}

export function resolveNavigationSurface(pathname: string): SurfaceTarget {
  if (CLIENT_NAV_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return "client";
  }
  if (pathname === "/") return "ceo";
  if (pathname === "/products") return "public";
  const mc = [
    "/finance",
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
    "/opportunities",
    "/acquisition",
    "/growth",
    "/tasks",
  ];
  if (mc.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return "ceo";
  }
  return "public";
}

/** Rule A — Customer Decision Engine: one path, no competing owner/catalog nav. */
export function isCustomerPurchasePath(pathname: string): boolean {
  return pathname === "/site" || pathname.startsWith("/site/") || pathname.startsWith("/order");
}

export const PUBLIC_NAV_LINKS = [
  { href: "/site", label: "Главная", match: (p: string, v: string) => p.startsWith("/site") && v !== "vector" },
  { href: "/site?view=vector", label: "Vector", match: (_p: string, v: string) => v === "vector" },
] as const;

export const CLIENT_NAV_LINKS = [
  { href: "/site", label: "Получить сайт", hint: "Guided Flow" },
  { href: "/site?view=vector", label: "Vector", hint: "Помощь в чате" },
  { href: "/projects", label: "Проекты", hint: "Мои результаты" },
] as const;

export const CEO_PRIMARY_LINKS = [
  { href: "/", label: "Пульт", hint: "Mission Control" },
  { href: "/create", label: "Factory", hint: "Создать продукт" },
  { href: "/finance", label: "Финансы", hint: "Деньги" },
  { href: "/company", label: "Стратегия", hint: "Компания" },
] as const;

export const CEO_STUDIO_LINKS = [
  { href: "/cursor", label: "Development", hint: "Cursor · код" },
  { href: "/acquisition", label: "Sales", hint: "Клиенты" },
  { href: "/ai", label: "AI Hub", hint: "Помощник" },
  { href: "/growth", label: "Аналитика", hint: "Рост" },
] as const;

export const CEO_SYSTEM_LINKS = [
  { href: "/launch", label: "Запуск", hint: "Сервисы" },
  { href: "/order", label: "Заказ", hint: "Клиентский" },
  { href: "/check", label: "Разработчик", hint: "Диагностика" },
  { href: "/settings", label: "Настройки", hint: "Профиль" },
] as const;
