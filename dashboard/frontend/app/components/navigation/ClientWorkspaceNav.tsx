"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import { CLIENT_NAV_LINKS } from "../../lib/surfaceNavConfig";

function isActive(pathname: string, href: string): boolean {
  if (href === "/client") return pathname === "/client";
  if (href === "/client/shop") {
    return pathname.startsWith("/client/shop") || pathname.startsWith("/client/stores");
  }
  if (href === "/client/bots") {
    return (
      pathname.startsWith("/client/bots") ||
      pathname.startsWith("/client/inbox") ||
      pathname.startsWith("/client/ai")
    );
  }
  if (href === "/client/site") {
    return pathname.startsWith("/client/site") || pathname.startsWith("/client/websites");
  }
  const base = href.split("?")[0];
  return pathname === base || pathname.startsWith(`${base}/`);
}

export function ClientWorkspaceNav() {
  const pathname = usePathname() ?? "";

  return (
    <aside className="genesis-sidebar virtus-surface-client" aria-label="Client navigation">
      <VirtusSurfaceIdentity surface="client" homeHref="/site" />

      <nav className="genesis-sidebar__nav">
        <div className="genesis-sidebar__section">
          <p className="genesis-sidebar__section-title">Business Control</p>
          <ul className="genesis-sidebar__list">
            {CLIENT_NAV_LINKS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`genesis-sidebar__link${active ? " is-active" : ""}`}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="genesis-sidebar__link-label">{item.label}</span>
                    {item.hint ? (
                      <span className="genesis-sidebar__link-hint">{item.hint}</span>
                    ) : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>

      <p className="genesis-sidebar__footer">Virtus Core · Ihr Kabinett</p>
    </aside>
  );
}
