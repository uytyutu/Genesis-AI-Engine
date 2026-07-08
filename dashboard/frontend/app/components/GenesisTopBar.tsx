"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../lib/publicBrand";

const TITLES: Record<string, string> = {
  "/": "Пульт управления",
  "/company": "Компания",
  "/finance": "Финансы",
  "/projects": "Проекты",
  "/cursor": "Development Studio",
  "/acquisition": "Sales Studio",
  "/ai": "AI Hub",
  "/growth": "Аналитика",
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

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME}</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        <Link href="/site" className="genesis-topbar__link">
          Сайт для клиентов
        </Link>
        <Link href="/create" className="genesis-topbar__cta">
          + Продукт
        </Link>
      </div>
    </header>
  );
}
