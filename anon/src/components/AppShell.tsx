"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AnonBootSplash } from "./AnonBootSplash";
import { BrandLogo } from "./BrandLogo";
import { useI18n } from "./I18nProvider";
import { SiteFooter } from "./SiteFooter";

type Me = {
  id: string;
  displayName: string;
  role: string;
  email?: string;
} | null;

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t, locale, setLocale, locales } = useI18n();
  const pathname = usePathname();
  const [me, setMe] = useState<Me>(null);
  const hideChrome = pathname?.startsWith("/open/") || pathname?.startsWith("/u/");

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include", cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setMe(d?.user ?? null))
      .catch(() => setMe(null));
  }, [pathname]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    setMe(null);
    window.location.href = "/";
  }

  const wide = Boolean(
    pathname?.startsWith("/r/") || pathname === "/games" || pathname === "/moments"
  );

  /** Mobile: Home · Secrets · Messages · Moments · Profile — games secondary */
  const mobileNav = [
    { href: "/", label: t("nav.home"), emoji: "⌂" },
    { href: "/loops", label: t("nav.leave"), emoji: "✨" },
    { href: "/secrets", label: t("nav.secrets"), emoji: "🔐" },
    { href: "/inbox", label: t("nav.messages"), emoji: "💬" },
    { href: me ? "/dashboard" : "/auth/login", label: t("nav.cabinet"), emoji: "👤" },
  ];

  return (
    <div className={wide ? "anon-shell anon-shell-wide" : "anon-shell"}>
      <AnonBootSplash />
      {!hideChrome && (
        <header className="mb-6 flex items-center justify-between gap-3">
          <BrandLogo variant="wordmark" size={34} />
          <div className="flex items-center gap-2">
            <Link
              href="/loops"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
            >
              {t("nav.leave")}
            </Link>
            <Link
              href="/secrets"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
            >
              {t("nav.secrets")}
            </Link>
            <Link
              href="/inbox"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
            >
              {t("nav.messages")}
            </Link>
            <Link
              href="/moments"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
            >
              {t("nav.moments")}
            </Link>
            <Link
              href="/games"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs md:!inline-flex"
            >
              {t("nav.games")}
            </Link>
            <Link
              href="/plus"
              className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs lg:!inline-flex"
            >
              {t("nav.plus")}
            </Link>
            {me?.role && ["owner", "admin", "moderator", "support", "analyst"].includes(me.role) ? (
              <Link
                href="/admin"
                className="anon-btn anon-btn-primary !px-3 !py-2 text-xs"
              >
                {t("admin.title")}
              </Link>
            ) : null}
            <label className="sr-only" htmlFor="lang">
              {t("footer.language")}
            </label>
            <select
              id="lang"
              className="rounded-xl border border-white/10 bg-black/30 px-2 py-1.5 text-xs"
              value={locale}
              onChange={(e) => setLocale(e.target.value as typeof locale)}
            >
              {locales.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                  {l.code === locale ? " ✓" : ""}
                </option>
              ))}
            </select>
            {me ? (
              <button
                type="button"
                onClick={logout}
                className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
              >
                {t("nav.logout")}
              </button>
            ) : (
              <Link
                href="/auth/login"
                className="anon-btn anon-btn-ghost !hidden !px-3 !py-2 text-xs sm:!inline-flex"
              >
                {t("nav.login")}
              </Link>
            )}
          </div>
        </header>
      )}
      {/* Minimal chrome on public profiles */}
      {pathname?.startsWith("/u/") && (
        <header className="mb-4 flex items-center justify-between">
          <BrandLogo variant="wordmark" size={28} />
          <Link href="/auth/register" className="text-xs text-violet-300 underline">
            {t("secret.getYourAnon")}
          </Link>
        </header>
      )}
      <div className={hideChrome && !pathname?.startsWith("/u/") ? "" : "pb-20 sm:pb-8"}>
        {children}
      </div>
      {!hideChrome && (
        <SiteFooter
          isAdmin={!!me?.role && ["owner", "admin", "moderator", "support", "analyst"].includes(me.role)}
        />
      )}
      {!hideChrome && (
        <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-violet-300/15 bg-[#1a1230]/92 backdrop-blur-xl sm:hidden">
          <ul className="mx-auto flex max-w-lg items-stretch justify-between px-1 py-2">
            {mobileNav.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname?.startsWith(item.href + "/");
              return (
                <li key={item.href} className="flex-1">
                  <Link
                    href={item.href}
                    className={`flex flex-col items-center gap-0.5 px-1 py-1 text-[10px] ${
                      active ? "text-white" : "text-white/45"
                    }`}
                  >
                    <span className="text-base">{item.emoji}</span>
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </div>
  );
}
