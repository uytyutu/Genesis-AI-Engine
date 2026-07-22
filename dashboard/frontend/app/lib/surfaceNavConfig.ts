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
  if (pathname === "/engine" || pathname.startsWith("/engine/")) return "ceo";
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
    "/journal",
    "/business",
    "/opportunities",
    "/acquisition",
    "/support",
    "/scanner",
    "/growth",
    "/tasks",
    "/tiktok-horizon",
    "/ceo-site",
  ];
  if (mc.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return "ceo";
  }
  if (pathname === "/scanner" || pathname.startsWith("/scanner/")) {
    return "ceo";
  }
  return "public";
}

/** Rule A — Customer Decision Engine: deprecated public purchase paths (Ramiš scanner mode). */
export function isCustomerPurchasePath(pathname: string): boolean {
  return false;
}

export type PublicNavLink = {
  href: string;
  label: string;
  match: (p: string) => boolean;
};

export const PUBLIC_NAV_LINKS: readonly PublicNavLink[] = [];

export const CLIENT_NAV_LINKS = [
  { href: "/projects", label: "Проекты", hint: "Мои результаты" },
  {
    href: "/projects/chatbot",
    label: "Vector",
    hint: "Dashboard · состояние",
  },
  {
    href: "/projects/chatbot/knowledge",
    label: "Knowledge",
    hint: "Факты о бизнесе",
  },
  {
    href: "/projects/chatbot/channels",
    label: "Channels",
    hint: "Где работает Vector",
  },
] as const;

export const CEO_PRIMARY_LINKS = [
  { href: "/business", label: "Бизнес", hint: "Mission 2 · KPI" },
  { href: "/acquisition", label: "Поиск лидов", hint: "Country Desk · все рынки · Path A" },
  { href: "/support", label: "Поддержка", hint: "Inbox · автоответы · шаблоны" },
  { href: "/ceo-site", label: "Сайт клиентов", hint: "Превью /site + /order" },
  { href: "/", label: "Ферма", hint: "Разметка · Toloka (не Desk)" },
  { href: "/journal", label: "Журнал", hint: "Доход · задачи" },
  { href: "/finance", label: "Финансы и налоги", hint: "Доходы · чеки · экспорт" },
] as const;

export const CEO_STUDIO_LINKS = [
  { href: "/cursor", label: "Разработка", hint: "Cursor · код" },
  { href: "/acquisition", label: "Country Desk", hint: "Все рынки · снайпер · Outbox" },
  { href: "/support", label: "Support", hint: "Inbox · Auto Rules · Templates" },
  { href: "/ceo-site", label: "Сайт клиентов", hint: "Как видит покупатель" },
  { href: "/tiktok-horizon", label: "Видео-фабрика", hint: "Horizon · TikTok · kill switch" },
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
