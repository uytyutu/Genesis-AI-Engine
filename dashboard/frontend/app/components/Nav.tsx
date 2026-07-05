"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { GenesisMark } from "./GenesisMark";

const ceoLinks = [
  { href: "/company", label: "Компания" },
  { href: "/finance", label: "Финансы" },
  { href: "/site", label: "Сайт для клиентов" },
  { href: "/projects", label: "Проекты" },
] as const;

const operatorLinks = [
  { href: "/launch", label: "Запуск" },
  { href: "/", label: "Пульт" },
  { href: "/order", label: "Заказ" },
  { href: "/check", label: "Разработчик" },
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="genesis-nav-bar mb-5 flex flex-col gap-3 px-3 py-3 sm:mb-6 sm:flex-row sm:items-center sm:justify-between sm:px-4">
      <Link href="/company" className="flex items-center gap-3">
        <GenesisMark className="h-9 w-9 shrink-0 shadow-glow" />
        <div>
          <p className="text-sm font-semibold tracking-tight">Genesis Company</p>
          <p className="text-[10px] text-genesis-muted sm:text-[11px]">Центр управления</p>
        </div>
      </Link>
      <nav className="-mx-1 flex gap-1 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible">
        {ceoLinks.map((link) => (
          <NavLink key={link.href} link={link} pathname={pathname} />
        ))}
        <span className="mx-1 hidden h-6 w-px self-center bg-genesis-border sm:inline" />
        {operatorLinks.map((link) => (
          <NavLink key={link.href} link={link} pathname={pathname} muted />
        ))}
      </nav>
    </header>
  );
}

function NavLink({
  link,
  pathname,
  muted,
}: {
  link: { href: string; label: string };
  pathname: string | null;
  muted?: boolean;
}) {
  const active =
    pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href + "/"));
  return (
    <Link
      href={link.href}
      className={`shrink-0 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-all sm:px-3 sm:text-xs ${
        active
          ? "bg-genesis-accent/15 text-white ring-1 ring-genesis-accent/40"
          : muted
            ? "text-genesis-muted/70 hover:bg-genesis-elevated/40 hover:text-genesis-muted"
            : "text-genesis-muted hover:bg-genesis-elevated/60 hover:text-white"
      }`}
    >
      {link.label}
    </Link>
  );
}
