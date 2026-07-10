"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { GenesisLogo } from "./GenesisLogo";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ASSISTANT_NAME } from "../lib/publicBrand";

export function PublicSiteHeader() {
  const { t } = useTranslation("common");
  const pathname = usePathname() ?? "";
  const searchParams = useSearchParams();
  const view = searchParams.get("view");
  const [open, setOpen] = useState(false);

  const onSite = pathname === "/site" || pathname.startsWith("/site/");
  const vectorView = onSite && view === "vector";

  const LINKS = [
    {
      href: "/site",
      label: t("nav.projects"),
      active: onSite && !vectorView,
    },
    {
      href: "/services",
      label: t("nav.services"),
      active: pathname === "/services" || pathname.startsWith("/services/"),
    },
    {
      href: "/site?view=vector",
      label: t("nav.vector"),
      active: vectorView,
    },
  ];

  return (
    <header className="relative mb-8 border-b border-white/5 pb-5">
      <div className="flex items-center justify-between gap-4">
        <GenesisLogo />
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <button
            type="button"
            className="rounded-xl border border-genesis-border-subtle px-3 py-2 text-sm text-genesis-muted transition-smooth hover:border-genesis-accent/30 hover:text-white sm:hidden"
            aria-expanded={open}
            aria-controls="public-nav"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? t("nav.close") : t("nav.menu")}
          </button>
        </div>
        <nav
          id="public-nav"
          className={`${open ? "flex" : "hidden"} absolute left-4 right-4 top-[4.5rem] z-20 flex-col gap-1 rounded-xl border border-genesis-border bg-genesis-panel p-3 shadow-card sm:static sm:flex sm:flex-row sm:items-center sm:gap-2 sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none`}
        >
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={`rounded-lg px-3 py-2 text-center text-sm transition-smooth hover:bg-genesis-elevated hover:text-white sm:text-left ${
                link.active
                  ? "bg-genesis-elevated/80 font-medium text-white"
                  : "text-genesis-muted"
              }`}
              aria-current={link.active ? "page" : undefined}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <p className="mt-3 hidden text-xs text-genesis-muted sm:block">
        {ASSISTANT_NAME} · Digital Company
      </p>
    </header>
  );
}
