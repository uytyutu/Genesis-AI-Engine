"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Mobile-first bottom tabs for Client Workspace (plan Slice 1). */
export const CLIENT_BOTTOM_NAV = [
  { href: "/client", label: "Home", match: (p: string) => p === "/client" },
  {
    href: "/client/products",
    label: "Website",
    match: (p: string) =>
      p.startsWith("/client/websites") ||
      (p.startsWith("/client/products") && !p.includes("store")),
  },
  {
    href: "/client/products",
    label: "Shop",
    match: (p: string) => p.startsWith("/client/stores"),
  },
  {
    href: "/client/orders",
    label: "Orders",
    match: (p: string) => p.startsWith("/client/orders"),
  },
  {
    href: "/client/shop",
    label: "More",
    match: (p: string) =>
      p.startsWith("/client/shop") ||
      p.startsWith("/client/billing") ||
      p.startsWith("/client/privacy") ||
      p.startsWith("/client/bots"),
  },
] as const;

export function ClientMobileNav() {
  const pathname = usePathname() ?? "";

  return (
    <nav className="genesis-mobile-nav genesis-mobile-nav--bottom" aria-label="Client mobile navigation">
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
