"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Mobile bottom tabs — short, same jobs as sidebar (Oracle-clear). */
export const CLIENT_BOTTOM_NAV = [
  { href: "/client", label: "Home", match: (p: string) => p === "/client" },
  {
    href: "/client/products",
    label: "Produkte",
    match: (p: string) =>
      p.startsWith("/client/products") ||
      p.startsWith("/client/websites") ||
      p.startsWith("/client/stores"),
  },
  {
    href: "/client/orders",
    label: "Bestellungen",
    match: (p: string) => p.startsWith("/client/orders"),
  },
  {
    href: "/client/shop",
    label: "Erweitern",
    match: (p: string) => p.startsWith("/client/shop"),
  },
  {
    href: "/client/support",
    label: "Hilfe",
    match: (p: string) =>
      p.startsWith("/client/support") ||
      p.startsWith("/client/billing") ||
      p.startsWith("/client/bots"),
  },
] as const;

export function ClientMobileNav() {
  const pathname = usePathname() ?? "";

  return (
    <nav
      className="genesis-mobile-nav genesis-mobile-nav--bottom"
      aria-label="Client mobile navigation"
    >
      {CLIENT_BOTTOM_NAV.map((link) => {
        const active = link.match(pathname);
        return (
          <Link
            key={`${link.href}-${link.label}`}
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
