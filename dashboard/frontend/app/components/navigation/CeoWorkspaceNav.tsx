"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import {
  CEO_PRIMARY_LINKS,
  CEO_STUDIO_LINKS,
  CEO_SYSTEM_LINKS,
} from "../../lib/surfaceNavConfig";
import { UI_LAYOUT, isMasterWorkshop } from "../../lib/uiLayout";

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function CeoWorkspaceNav() {
  const pathname = usePathname() ?? "";
  const master = isMasterWorkshop();

  const primary = master
    ? CEO_PRIMARY_LINKS.map((item) =>
        item.href === "/" ? { ...item, label: UI_LAYOUT.home_label, hint: "DRY RUN · local" } : item,
      ).filter((item) => ["/", "/opportunities", "/finance", "/settings"].includes(item.href))
    : CEO_PRIMARY_LINKS;

  const sections = master
    ? [
        { title: "Мастерская", items: primary },
        { title: "Система", items: CEO_SYSTEM_LINKS.filter((i) => i.href === "/settings") },
      ]
    : [
        { title: "Решения", items: CEO_PRIMARY_LINKS },
        { title: "Студии", items: CEO_STUDIO_LINKS },
        { title: "Система", items: CEO_SYSTEM_LINKS },
      ];

  return (
    <aside
      className={`genesis-sidebar virtus-surface-ceo${UI_LAYOUT.compact_sidebar ? " genesis-sidebar--compact" : ""}`}
      aria-label="CEO navigation"
      style={UI_LAYOUT.compact_sidebar ? { width: UI_LAYOUT.sidebar_width_px } : undefined}
    >
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
                      {item.hint && !UI_LAYOUT.hide_link_hints ? (
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

      <p className="genesis-sidebar__footer">{UI_LAYOUT.label} · Vector</p>
    </aside>
  );
}
