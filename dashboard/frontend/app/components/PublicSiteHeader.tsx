"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { VirtusSurfaceIdentity } from "./navigation/VirtusSurfaceIdentity";
import { PublicWorkspaceNav } from "./navigation/PublicWorkspaceNav";
import { PUBLIC_NAV_LINKS } from "../lib/surfaceNavConfig";

export function PublicSiteHeader({ customerDecisionFlow = false }: { customerDecisionFlow?: boolean }) {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const hasPublicNav = PUBLIC_NAV_LINKS.length > 0;
  const showMenu = !customerDecisionFlow && hasPublicNav;

  return (
    <header className={`relative border-b border-white/5 pb-5 ${customerDecisionFlow ? "mb-4" : "mb-8"}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <VirtusSurfaceIdentity surface="public" homeHref="/site" />
        </div>
        <div className="flex shrink-0 items-center gap-2 pt-1">
          <LanguageSwitcher compact />
          {showMenu ? (
            <button
              type="button"
              className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-xl border border-genesis-border-subtle px-3 py-2 text-sm text-genesis-muted transition-smooth hover:border-genesis-accent/30 hover:text-white sm:hidden"
              aria-expanded={open}
              aria-controls="public-nav"
              aria-label={open ? t("nav.close") : t("nav.menu")}
              onClick={() => setOpen((v) => !v)}
            >
              <span aria-hidden className="text-base leading-none">
                {open ? "✕" : "☰"}
              </span>
            </button>
          ) : null}
        </div>
      </div>
      {showMenu ? (
        <nav
          id="public-nav"
          aria-label="Public navigation"
          className={`${open ? "flex" : "hidden"} mt-4 flex-col gap-1 rounded-xl border border-genesis-border bg-genesis-panel p-3 shadow-card sm:mt-5 sm:flex sm:flex-row sm:items-center sm:gap-2 sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none`}
        >
          <PublicWorkspaceNav onNavigate={() => setOpen(false)} />
        </nav>
      ) : null}
    </header>
  );
}
