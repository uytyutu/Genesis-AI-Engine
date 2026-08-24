"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { bccMobileNav } from "../../lib/workspaceNav";

/** Mobile bottom tabs — BCC essentials (aligned with sidebar). */
export function ClientMobileNav() {
  const pathname = usePathname() ?? "";
  const links = bccMobileNav();

  return (
    <nav
      className="genesis-mobile-nav genesis-mobile-nav--bottom"
      aria-label="Client mobile navigation"
    >
      {links.map((link) => {
        const active = link.match(pathname);
        return (
          <Link
            key={link.id}
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
