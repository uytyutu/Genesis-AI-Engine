"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import { MC_NAV_SECTIONS } from "../../lib/surfaceNavConfig";
import { UI_LAYOUT } from "../../lib/uiLayout";

function isActive(pathname: string, href: string): boolean {
  if (href === "/executive") return pathname === "/executive";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function CeoWorkspaceNav() {
  const pathname = usePathname() ?? "";

  return (
    <aside
      className={`genesis-sidebar virtus-surface-ceo${UI_LAYOUT.compact_sidebar ? " genesis-sidebar--compact" : ""}`}
      aria-label="Mission Control navigation"
      style={UI_LAYOUT.compact_sidebar ? { width: UI_LAYOUT.sidebar_width_px } : undefined}
    >
      <VirtusSurfaceIdentity surface="ceo" homeHref="/executive" />
      <p className="genesis-sidebar__section-title" style={{ padding: "8px 12px 0" }}>
        Mission Control
      </p>

      <nav className="genesis-sidebar__nav">
        {MC_NAV_SECTIONS.map((section) => (
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
    </aside>
  );
}
