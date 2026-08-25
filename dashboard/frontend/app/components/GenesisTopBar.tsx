"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../lib/publicBrand";

const TITLES: Record<string, string> = {
  "/executive": "Обзор",
  "/executive-legacy": "Старый CEO Dashboard",
  "/orders": "Заказы",
  "/factory": "Продукты",
  "/clients": "Клиенты",
  "/support": "Поддержка",
  "/finance": "Финансы",
  "/acquisition": "Продажи · Country Desk",
  "/farm": "Студия · Ферма",
  "/farm-engine": "Студия · Farm Engine",
  "/ai": "Vector",
  "/launch": "Запуск",
  "/check": "Здоровье системы",
  "/monitor": "Монитор",
  "/settings": "Настройки",
  "/ceo-site": "Публичный сайт",
  "/create": "Factory Wizard",
  "/": "Обзор",
};

function titleForPath(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  const base = `/${pathname.split("/").filter(Boolean)[0] ?? ""}`;
  return TITLES[base] ?? BRAND_NAME;
}

/** Quiet owner topbar — no Farm CTAs. */
export function GenesisTopBar() {
  const pathname = usePathname() ?? "/";
  const title = titleForPath(pathname);

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME} · Mission Control</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        <Link href="/clients" className="genesis-topbar__link">
          Клиенты
        </Link>
        <Link href="/orders" className="genesis-topbar__link">
          Заказы
        </Link>
        <Link href="/executive" className="genesis-topbar__cta">
          Обзор
        </Link>
      </div>
    </header>
  );
}
