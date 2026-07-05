"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const MOBILE_LINKS = [
  { href: "/", label: "Пульт" },
  { href: "/company", label: "Компания" },
  { href: "/finance", label: "Финансы" },
  { href: "/cursor", label: "Dev" },
  { href: "/acquisition", label: "Sales" },
  { href: "/settings", label: "⚙" },
] as const;

export function GenesisMobileNav() {
  const pathname = usePathname() ?? "";

  return (
    <nav className="genesis-mobile-nav" aria-label="Mobile navigation">
      {MOBILE_LINKS.map((link) => {
        const active =
          pathname === link.href ||
          (link.href !== "/" && pathname.startsWith(`${link.href}/`));
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`genesis-mobile-nav__link${active ? " is-active" : ""}`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
