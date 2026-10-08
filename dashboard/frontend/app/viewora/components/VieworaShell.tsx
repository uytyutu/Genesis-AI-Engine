"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import "../viewora.css";

export function VieworaShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const slim = pathname.includes("/legal/");

  return (
    <div className="viewora">
      {/*
        THESIS: Sell finished content outcomes, not model pickers — refuse generic AI-tool dashboards.
        OWN-WORLD: Night color-suite · coral pulse · vertical phone as proof surface · Bricolage + Source Sans 3.
        STORY: Visitor describes desire → CREATE → modes/DNA/hooks/Watchability → paid plan.
        FIRST VIEWPORT: Brand Virtus Video AI · headline · one prompt · CREATE · phone preview.
        FORM: Vertical attention lab · seed:owner-brief-2026-virtus-video-ai
        FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
      */}
      <div className="viewora-shell">
        <header className="viewora-nav">
          <Link href="/viewora" className="viewora-brand">
            Virtus <span>Video AI</span>
          </Link>
          {!slim ? (
            <nav className="viewora-nav-links" aria-label="Virtus Video AI">
              <Link href="/viewora/create">Studio</Link>
              <Link href="/viewora/pricing">Pricing</Link>
              <Link href="/viewora#features">Features</Link>
              <Link href="/viewora/create" className="viewora-btn viewora-btn-primary">
                Create
              </Link>
            </nav>
          ) : (
            <nav className="viewora-nav-links">
              <Link href="/viewora">← Back</Link>
            </nav>
          )}
        </header>
        <main id="main-content">{children}</main>
        <footer className="viewora-footer">
          <div>
            <strong style={{ color: "var(--vo-text)" }}>Virtus Video AI</strong> by Virtus Core —
            professional AI Content Studio. You describe or upload; we turn it into content people
            watch.
          </div>
          <div className="viewora-footer-links">
            <Link href="/viewora/pricing">Pricing</Link>
            <Link href="/viewora/legal/impressum">Impressum</Link>
            <Link href="/viewora/legal/datenschutz">Datenschutz</Link>
            <Link href="/viewora/legal/agb">AGB</Link>
            <Link href="/viewora/legal/ki-hinweis">KI-Hinweis</Link>
            <Link href="/site">Virtus Core</Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
