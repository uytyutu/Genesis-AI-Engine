"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import {
  CEO_PRIMARY_LINKS,
  CEO_STUDIO_LINKS,
  CEO_SYSTEM_LINKS,
} from "../../lib/surfaceNavConfig";

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function CeoWorkspaceNav() {
  const pathname = usePathname() ?? "";

  const sections = [
    { title: "Решения", items: CEO_PRIMARY_LINKS },
    { title: "Студии", items: CEO_STUDIO_LINKS },
    { title: "Система", items: CEO_SYSTEM_LINKS },
  ];

  return (
    <aside className="genesis-sidebar virtus-surface-ceo" aria-label="CEO navigation">
      <VirtusSurfaceIdentity surface="ceo" homeHref="/" />

      <nav className="genesis-sidebar__nav">
        {sections.map((section) => (
          <div key={section.title} className="genesis-sidebar__section">
            <p className="genesis-sidebar__section-title">{section.title}</p>
            <ul className="genesis-sidebar__list">
              {section.items.map((item) => {
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
        ))}
      </nav>

      <p className="genesis-sidebar__footer">Virtus Core · Vector</p>
    </aside>
  );
}
