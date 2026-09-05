"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { DM_Sans, Fraunces } from "next/font/google";
import { OFFICE_I18N_LOCALES } from "../../lib/officeI18n";
import { useOfficeT } from "../../lib/useOfficeT";
import "./office-shell.css";

const dmSans = DM_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--vo-font-sans",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin", "latin-ext"],
  variable: "--vo-font-display",
  display: "swap",
});

const NAV = [
  { href: "/office", key: "home" },
  { href: "/office/translate", key: "translate" },
  { href: "/office/lebenslauf", key: "lebenslauf" },
  { href: "/office/bewerbung", key: "bewerbung" },
  { href: "/office/documents", key: "documents" },
  { href: "/office/excel", key: "excel" },
  { href: "/office/smart", key: "smart" },
  { href: "/office/cabinet", key: "cabinet" },
] as const;

export function OfficeShell({
  children,
  active,
}: {
  children: ReactNode;
  active?: string;
}) {
  const { t, locale, setOfficeLocale } = useOfficeT();

  return (
    <div className={`${dmSans.variable} ${fraunces.variable} vo-shell`}>
      <div className="vo-ambient" aria-hidden="true">
        <span className="vo-ambient__grid" />
        <span className="vo-ambient__sheet vo-ambient__sheet--a" />
        <span className="vo-ambient__sheet vo-ambient__sheet--b" />
        <span className="vo-ambient__sheet vo-ambient__sheet--c" />
        <span className="vo-ambient__line vo-ambient__line--1" />
        <span className="vo-ambient__line vo-ambient__line--2" />
        <span className="vo-ambient__ink vo-ambient__ink--1" />
        <span className="vo-ambient__ink vo-ambient__ink--2" />
      </div>
      <header className="border-b border-[var(--vo-border)] bg-[var(--vo-surface)]/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link
            href="/office"
            className="vo-display text-xl font-semibold tracking-tight text-[var(--vo-ink)]"
          >
            {t("brand")}
          </Link>
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-2.5 py-1.5 transition ${
                  active === item.key
                    ? "bg-[var(--vo-accent-soft)] font-semibold text-[var(--vo-accent)]"
                    : "text-[var(--vo-muted)] hover:bg-black/[0.03] hover:text-[var(--vo-ink)]"
                }`}
              >
                {t(`nav.${item.key}`)}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <label className="sr-only" htmlFor="vo-lang">
              {t("uiLangLabel")}
            </label>
            <select
              id="vo-lang"
              value={locale}
              onChange={(e) =>
                setOfficeLocale(e.target.value as (typeof OFFICE_I18N_LOCALES)[number])
              }
              className="rounded-lg border border-[var(--vo-border)] bg-[var(--vo-surface)] px-2 py-1.5 text-xs text-[var(--vo-ink)]"
            >
              {OFFICE_I18N_LOCALES.map((code) => (
                <option key={code} value={code}>
                  {code.toUpperCase()}
                </option>
              ))}
            </select>
            <Link
              href="/site"
              className="text-xs text-[var(--vo-muted)] underline-offset-2 hover:text-[var(--vo-ink)] hover:underline"
            >
              {t("backCore")}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10 sm:py-14">{children}</main>

      <footer className="border-t border-[var(--vo-border)] bg-[var(--vo-surface)]/70">
        <div className="mx-auto grid max-w-5xl gap-6 px-4 py-8 text-xs text-[var(--vo-muted)] sm:grid-cols-2">
          <div>
            <p className="font-semibold text-[var(--vo-ink)]">{t("footer.privacyTitle")}</p>
            <p className="mt-1 leading-relaxed">{t("footer.privacyBody")}</p>
          </div>
          <div>
            <p className="font-semibold text-[var(--vo-ink)]">{t("footer.legalTitle")}</p>
            <p className="mt-1 leading-relaxed">{t("footer.legalBody")}</p>
            <p className="mt-2 leading-relaxed">{t("customerNotice")}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
