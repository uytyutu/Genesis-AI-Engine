"use client";

import type { CSSProperties } from "react";

/**
 * Full-viewport storefront wash.
 * Must be SSR-identical to the first client paint — never gate on `mounted`
 * (that caused mobile whole-page flicker: plain shell → GPU layers appear).
 * Rendered as a fixed sibling outside `.storefront` isolate (see PublicPageShell).
 */
export function StorefrontAtmosphere() {
  return (
    <div className="storefront-page-bg" aria-hidden>
      <div className="storefront-page-bg__base" />
      <div className="storefront-page-bg__mesh" />
      <div className="storefront-page-bg__aurora storefront-page-bg__aurora--a" />
      <div className="storefront-page-bg__aurora storefront-page-bg__aurora--b" />
      <div className="storefront-page-bg__aurora storefront-page-bg__aurora--c" />
      <div className="storefront-page-bg__grid" />
      <div className="storefront-page-bg__orb storefront-page-bg__orb--a" />
      <div className="storefront-page-bg__orb storefront-page-bg__orb--b" />
      <div className="storefront-page-bg__orb storefront-page-bg__orb--c" />
      <div className="storefront-page-bg__orb storefront-page-bg__orb--d" />
      <div className="storefront-page-bg__particles">
        {Array.from({ length: 22 }, (_, i) => (
          <span
            key={i}
            className="storefront-page-bg__particle"
            style={
              {
                "--sx": `${4 + ((i * 17) % 90)}%`,
                "--sy": `${6 + ((i * 23) % 86)}%`,
                "--dur": `${9 + (i % 8) * 1.35}s`,
                "--delay": `${(i % 10) * -1.05}s`,
                "--size": `${2 + (i % 4)}px`,
              } as CSSProperties
            }
          />
        ))}
      </div>
      <div className="storefront-page-bg__vignette" />
    </div>
  );
}
