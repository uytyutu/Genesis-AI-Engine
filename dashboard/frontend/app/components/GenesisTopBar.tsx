"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../lib/publicBrand";

const TITLES: Record<string, string> = {
  "/business": "Business Health",
  "/business/kpi": "Mission 2 · KPI",
  "/": "Labeling Farm",
  "/journal": "Журнал",
  "/company": "Компания",
  "/finance": "Finanzen & Steuer",
  "/projects": "Проекты",
  "/cursor": "Development Studio",
  "/acquisition": "Country Desk · DE",
  "/ceo-site": "Сайт клиентов",
  "/tiktok-horizon": "Video Factory",
  "/ai": "AI Hub",
  "/growth": "Mission 2 · Конверсия",
  "/launch": "Запуск",
  "/order": "Заказ",
  "/check": "Разработчик",
  "/settings": "Настройки",
  "/create": "Factory",
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

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME}</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        <Link href="/ceo-site" className="genesis-topbar__link">
          Сайт клиентов
        </Link>
        <Link href="/acquisition" className="genesis-topbar__link">
          Country Desk
        </Link>
        <Link href="/order" className="genesis-topbar__cta">
          /order
        </Link>
      </div>
    </header>
  );
}
