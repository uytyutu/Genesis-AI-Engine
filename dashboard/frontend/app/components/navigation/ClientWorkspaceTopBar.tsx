"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../../lib/publicBrand";

/** BCC top bar — German only (client chrome, not i18n-locale dependent). */
const TITLES: Record<string, string> = {
  "/client": "Übersicht",
  "/client/products": "Meine Produkte",
  "/client/site": "Website",
  "/client/shop": "Shop",
  "/client/bots": "AI",
  "/client/inbox": "Posteingang",
  "/client/settings": "Business",
  "/client/billing": "Abrechnung",
  "/client/support": "Support",
  "/client/orders": "Bestellungen",
  "/client/downloads": "Downloads",
  "/projects": "Projekte",
  "/create": "Erstellen",
};

function resolveTitle(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "client" && parts[1]) {
    const hub = `/client/${parts[1]}`;
    if (TITLES[hub]) return TITLES[hub];
  }
  return "Mein Unternehmen";
}

export function ClientWorkspaceTopBar() {
  const pathname = usePathname() ?? "/";
  const title = resolveTitle(pathname);

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME}</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        <Link href="/site" className="genesis-topbar__cta">
          Vector
        </Link>
      </div>
    </header>
  );
}
