"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CLIENT_NAV_LINKS } from "../../lib/surfaceNavConfig";

export function ClientMobileNav() {
  const pathname = usePathname() ?? "";

  return (
    <nav className="genesis-mobile-nav" aria-label="Client mobile navigation">
      {CLIENT_NAV_LINKS.map((link) => {
        const base = link.href.split("?")[0];
        const active = pathname === base || pathname.startsWith(`${base}/`);
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
