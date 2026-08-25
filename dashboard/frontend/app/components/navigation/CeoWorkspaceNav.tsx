"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { VirtusSurfaceIdentity } from "./VirtusSurfaceIdentity";
import {
  CEO_PRIMARY_LINKS,
  CEO_STUDIO_LINKS,
  CEO_SYSTEM_LINKS,
} from "../../lib/surfaceNavConfig";
import { UI_LAYOUT } from "../../lib/uiLayout";

function isActive(pathname: string, href: string): boolean {
  if (href === "/executive") {
    return pathname === "/executive" || pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Clean Owner Mission Control shell — commercial Virtus only. */
export function CeoWorkspaceNav() {
  const pathname = usePathname() ?? "";
  const studioOpenDefault = CEO_STUDIO_LINKS.some((item) =>
    isActive(pathname, item.href),
  );
  const [studiosOpen, setStudiosOpen] = useState(studioOpenDefault);

  return (
    <aside
      className={`genesis-sidebar virtus-surface-ceo${UI_LAYOUT.compact_sidebar ? " genesis-sidebar--compact" : ""}`}
      aria-label="Mission Control"
      style={
        UI_LAYOUT.compact_sidebar
          ? { width: UI_LAYOUT.sidebar_width_px }
          : undefined
      }
    >
      <VirtusSurfaceIdentity surface="ceo" homeHref="/executive" />

      <nav className="genesis-sidebar__nav">
        <div className="genesis-sidebar__section">
          <p className="genesis-sidebar__section-title">Компания</p>
          <ul className="genesis-sidebar__list">
            {CEO_PRIMARY_LINKS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`genesis-sidebar__link${active ? " is-active" : ""}`}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="genesis-sidebar__link-label">{item.label}</span>
                    {!UI_LAYOUT.hide_link_hints && item.hint ? (
                      <span className="genesis-sidebar__link-hint">{item.hint}</span>
                    ) : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="genesis-sidebar__section">
          <button
            type="button"
            className="genesis-sidebar__section-title flex w-full items-center justify-between text-left"
            onClick={() => setStudiosOpen((v) => !v)}
            aria-expanded={studiosOpen}
          >
            <span>Студии</span>
            <span className="text-[10px] font-normal text-zinc-500">
              {studiosOpen ? "▾" : "▸"} Labs
            </span>
          </button>
          {studiosOpen ? (
            <ul className="genesis-sidebar__list">
              {CEO_STUDIO_LINKS.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`genesis-sidebar__link${active ? " is-active" : ""}`}
                      aria-current={active ? "page" : undefined}
                    >
                      <span className="genesis-sidebar__link-label">
                        {item.label}
                      </span>
                      {!UI_LAYOUT.hide_link_hints && item.hint ? (
                        <span className="genesis-sidebar__link-hint">
                          {item.hint}
                        </span>
                      ) : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="px-3 pb-2 text-[10px] leading-snug text-zinc-600">
              Ферма, Alpha Hunter и старые labs — здесь, не на главной.
            </p>
          )}
        </div>

        <div className="genesis-sidebar__section">
          <p className="genesis-sidebar__section-title">Система</p>
          <ul className="genesis-sidebar__list">
            {CEO_SYSTEM_LINKS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`genesis-sidebar__link${active ? " is-active" : ""}`}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="genesis-sidebar__link-label">{item.label}</span>
                    {!UI_LAYOUT.hide_link_hints && item.hint ? (
                      <span className="genesis-sidebar__link-hint">{item.hint}</span>
                    ) : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>

      <p className="genesis-sidebar__footer">Virtus Core · Mission Control</p>
    </aside>
  );
}
