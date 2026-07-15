"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../lib/publicBrand";

const TITLES: Record<string, string> = {
  "/business": "Business Health",
  "/business/kpi": "Mission 2 · KPI",
  "/": "Цифровая ферма",
  "/journal": "Журнал",
  "/company": "Компания",
  "/finance": "Финансы",
  "/projects": "Проекты",
  "/cursor": "Development Studio",
  "/acquisition": "Sales Studio",
  "/ai": "AI Hub",
  "/growth": "Mission 2 · Конверсия",
  "/launch": "Запуск",
  "/order": "Заказ",
  "/check": "Разработчик",
  "/settings": "Настройки",
  "/create": "Создать продукт",
  "/opportunities": "Возможности",
  "/monitor": "Мониторинг",
  "/tasks": "Задачи",
};

function titleForPath(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  const base = `/${pathname.split("/").filter(Boolean)[0] ?? ""}`;
  return TITLES[base] ?? BRAND_NAME;
}

export function GenesisTopBar() {
  const pathname = usePathname() ?? "/";
  const title = titleForPath(pathname);
  const businessFocus =
    pathname === "/business" ||
    pathname.startsWith("/business/") ||
    pathname === "/growth" ||
    pathname === "/acquisition" ||
    pathname === "/finance";

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME}</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        {!businessFocus ? (
          <>
            <Link href="/site" className="genesis-topbar__link">
              Сайт для клиентов
            </Link>
            <Link href="/create" className="genesis-topbar__cta">
              + Продукт
            </Link>
          </>
        ) : (
          <>
            <Link href="/acquisition" className="genesis-topbar__link">
              Outbox
            </Link>
            <Link href="/finance" className="genesis-topbar__cta">
              Финансы
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
