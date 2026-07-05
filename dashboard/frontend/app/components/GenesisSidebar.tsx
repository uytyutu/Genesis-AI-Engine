"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { GenesisMark } from "./GenesisMark";

type NavItem = { href: string; label: string; hint?: string };

const SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: "Genesis",
    items: [
      { href: "/", label: "Пульт", hint: "Главный экран" },
      { href: "/company", label: "Компания", hint: "Обзор" },
      { href: "/finance", label: "Финансы", hint: "Деньги" },
      { href: "/projects", label: "Проекты", hint: "Продукты" },
    ],
  },
  {
    title: "Студии",
    items: [
      { href: "/cursor", label: "Development", hint: "Cursor · код" },
      { href: "/acquisition", label: "Sales", hint: "Клиенты" },
      { href: "/ai", label: "AI Hub", hint: "Помощник" },
      { href: "/growth", label: "Аналитика", hint: "Рост" },
    ],
  },
  {
    title: "Система",
    items: [
      { href: "/launch", label: "Запуск", hint: "Сервисы" },
      { href: "/order", label: "Заказ", hint: "Клиентский" },
      { href: "/check", label: "Разработчик", hint: "Диагностика" },
      { href: "/settings", label: "Настройки", hint: "Профиль" },
    ],
  },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function GenesisSidebar() {
  const pathname = usePathname() ?? "";

  return (
    <aside className="genesis-sidebar" aria-label="Genesis navigation">
      <Link href="/" className="genesis-sidebar__brand">
        <GenesisMark className="h-10 w-10 shrink-0 shadow-glow" />
        <div className="min-w-0">
          <p className="genesis-sidebar__name">Genesis</p>
          <p className="genesis-sidebar__tag">Company OS</p>
        </div>
      </Link>

      <nav className="genesis-sidebar__nav">
        {SECTIONS.map((section) => (
          <div key={section.title} className="genesis-sidebar__section">
            <p className="genesis-sidebar__section-title">{section.title}</p>
            <ul className="genesis-sidebar__list">
              {section.items.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`genesis-sidebar__link${active ? " is-active" : ""}`}
                      aria-current={active ? "page" : undefined}
                    >
                      <span className="genesis-sidebar__link-label">{item.label}</span>
                      {item.hint && (
                        <span className="genesis-sidebar__link-hint">{item.hint}</span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <p className="genesis-sidebar__footer">Brand v1.0 · Orbit Stack</p>
    </aside>
  );
}
