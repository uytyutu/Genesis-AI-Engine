"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { GenesisLogo } from "./GenesisLogo";
import { ButtonLink } from "./ui/Button";

const LINKS = [
  { href: "/site", label: "Главная" },
  { href: "/services", label: "Услуги" },
  { href: "/products", label: "Studio" },
  { href: "/order", label: "Заказать", accent: true },
];

export function PublicSiteHeader() {
  const pathname = usePathname() ?? "";
  const [open, setOpen] = useState(false);

  return (
    <header className="relative mb-8 border-b border-white/5 pb-5">
      <div className="flex items-center justify-between gap-4">
        <GenesisLogo />
        <button
          type="button"
          className="rounded-xl border border-genesis-border-subtle px-3 py-2 text-sm text-genesis-muted transition-smooth hover:border-genesis-accent/30 hover:text-white sm:hidden"
          aria-expanded={open}
          aria-controls="public-nav"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Закрыть" : "Меню"}
        </button>
        <nav
          id="public-nav"
          className={`${open ? "flex" : "hidden"} absolute left-4 right-4 top-[4.5rem] z-20 flex-col gap-1 rounded-xl border border-genesis-border bg-genesis-panel p-3 shadow-card sm:static sm:flex sm:flex-row sm:items-center sm:gap-2 sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none`}
        >
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            if (link.accent) {
              return (
                <ButtonLink
                  key={link.href}
                  href={link.href}
                  variant="primary"
                  size="sm"
                  className="text-center shadow-glow"
                  onClick={() => setOpen(false)}
                >
                  {link.label}
                </ButtonLink>
              );
            }
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2 text-center text-sm transition-smooth hover:bg-genesis-elevated hover:text-white sm:text-left ${
                  active ? "text-white" : "text-genesis-muted"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
