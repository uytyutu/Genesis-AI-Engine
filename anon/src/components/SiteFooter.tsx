"use client";

import Link from "next/link";
import { useI18n } from "./I18nProvider";

export function SiteFooter({ isAdmin }: { isAdmin?: boolean }) {
  const { t, locale, setLocale, locales } = useI18n();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-white/10 pt-8 pb-2">
      <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-sm font-bold tracking-[0.22em]">ANON</p>
          <p className="mt-2 text-sm text-white/90">{t("brand.secretHero")}</p>
          <p className="mt-2 text-xs anon-muted">{t("footer.tagline")}</p>
        </div>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] anon-muted">
            {t("footer.product")}
          </p>
          <nav className="flex flex-col gap-2 text-sm">
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/secrets"
            >
              🔐 {t("nav.secrets")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/drop"
            >
              🔥 {t("product.drop")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/create"
            >
              💌 {t("product.moment")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/open-when"
            >
              🔒 {t("product.openLater")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/games"
            >
              🎮 {t("footer.play")}
            </Link>
            <Link
              className="hover:text-white/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 text-white/55"
              href="/dna"
            >
              🧬 {t("dna.footer")}
            </Link>
          </nav>
        </div>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] anon-muted">
            {t("footer.legal")}
          </p>
          <nav className="flex flex-col gap-2 text-sm">
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/impressum"
            >
              {t("legal.impressum")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/datenschutz"
            >
              {t("legal.datenschutz")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/cookies"
            >
              {t("legal.cookies")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/agb"
            >
              {t("legal.agb")}
            </Link>
          </nav>
        </div>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] anon-muted">
            {t("footer.support")}
          </p>
          <nav className="flex flex-col gap-2 text-sm">
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/help"
            >
              {t("footer.help")}
            </Link>
            <Link
              className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              href="/contact"
            >
              {t("footer.contact")}
            </Link>
            {isAdmin && (
              <Link
                className="hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
                href="/admin"
              >
                {t("admin.title")}
              </Link>
            )}
          </nav>
          <label className="mt-4 block text-xs anon-muted" htmlFor="footer-lang">
            {t("footer.language")}
          </label>
          <select
            id="footer-lang"
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-2 py-1.5 text-xs"
            value={locale}
            onChange={(e) => setLocale(e.target.value as typeof locale)}
          >
            {locales.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 border-t border-white/5 pt-4 text-xs anon-muted">
        <span>© {year} ANON</span>
        <span aria-hidden>·</span>
        <Link href="/impressum" className="hover:text-white underline-offset-2 hover:underline">
          {t("legal.impressum")}
        </Link>
        <span aria-hidden>·</span>
        <Link href="/datenschutz" className="hover:text-white underline-offset-2 hover:underline">
          {t("legal.datenschutz")}
        </Link>
        <span aria-hidden>·</span>
        <Link href="/agb" className="hover:text-white underline-offset-2 hover:underline">
          {t("legal.agb")}
        </Link>
      </div>
    </footer>
  );
}
