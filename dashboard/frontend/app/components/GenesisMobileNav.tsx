"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MC_PULT_LINKS } from "../lib/surfaceNavConfig";

export function GenesisMobileNav() {
  const pathname = usePathname() ?? "";
  const links = MC_PULT_LINKS;

  return (
    <nav className="genesis-mobile-nav" aria-label="CEO mobile navigation">
      {links.map((link) => {
        const active =
          pathname === link.href ||
          (link.href.length > 1 && pathname.startsWith(`${link.href}/`));
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
