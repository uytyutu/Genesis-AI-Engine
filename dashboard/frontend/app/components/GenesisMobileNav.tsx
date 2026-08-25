"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CEO_PRIMARY_LINKS } from "../lib/surfaceNavConfig";

/** Mobile: только коммерческий Virtus (без Farm). */
export function GenesisMobileNav() {
  const pathname = usePathname() ?? "";
  const primary = CEO_PRIMARY_LINKS.slice(0, 5);

  return (
    <nav className="genesis-mobile-nav" aria-label="Mission Control mobile">
      {primary.map((link) => {
        const active =
          link.href === "/executive"
            ? pathname === "/executive" || pathname === "/"
            : pathname === link.href || pathname.startsWith(`${link.href}/`);
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
