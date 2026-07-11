"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import { CLIENT_NAV_LINKS } from "../../lib/surfaceNavConfig";

function isActive(pathname: string, href: string): boolean {
  if (href.includes("?")) {
    return pathname === "/site" || pathname.startsWith("/site/");
  }
  if (href === "/") return pathname === "/";
  const base = href.split("?")[0];
  return pathname === base || pathname.startsWith(`${base}/`);
}

export function ClientWorkspaceNav() {
  const pathname = usePathname() ?? "";

  return (
    <aside className="genesis-sidebar virtus-surface-client" aria-label="Client navigation">
      <VirtusSurfaceIdentity surface="client" homeHref="/site?view=vector" />

      <nav className="genesis-sidebar__nav">
        <div className="genesis-sidebar__section">
          <p className="genesis-sidebar__section-title">Моя компания</p>
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

      <p className="genesis-sidebar__footer">{CLIENT_NAV_LINKS[0].label} ведёт процесс</p>
    </aside>
  );
}
