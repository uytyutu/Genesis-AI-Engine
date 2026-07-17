"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";

/**
 * Public Path A storefront — DE-first via i18n (browser locale + LanguageSwitcher).
 */
export function SitePage() {
  const { t } = useTranslation("site");

  return (
    <PublicPageShell>
      <div className="mx-auto max-w-3xl space-y-10 py-6 animate-fade-up">
        <header className="space-y-4 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/90">
            {t("pathA.eyebrow", { brand: BRAND_NAME })}
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t("pathA.title")}
          </h1>
          <p className="mx-auto max-w-2xl text-base text-genesis-muted sm:text-lg">
            {t("pathA.subtitle")}
          </p>
          <ul className="mx-auto flex max-w-xl flex-wrap justify-center gap-2 text-xs sm:text-sm">
            {[t("pathA.benefitMobile"), t("pathA.benefitSeo"), t("pathA.benefitSpeed")].map(
              (label) => (
                <li
                  key={label}
                  className="rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1.5 text-emerald-100/90"
                >
                  ✓ {label}
                </li>
              ),
            )}
          </ul>
        </header>

        <section className="grid gap-3 sm:grid-cols-3">
          {[
            { name: "Basic", price: "350 €", noteKey: "pathA.pkgBasic" },
            { name: "Business", price: "650 €", noteKey: "pathA.pkgBusiness" },
            { name: "Premium", price: "1 200 €", noteKey: "pathA.pkgPremium" },
          ].map((p) => (
            <div
              key={p.name}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-center"
            >
              <p className="text-sm text-genesis-muted">{p.name}</p>
              <p className="mt-1 text-2xl font-semibold text-white">{p.price}</p>
              <p className="mt-1 text-xs text-white/60">{t(p.noteKey)}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("pathA.whatTitle")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• {t("pathA.what1")}</li>
            <li>• {t("pathA.what2")}</li>
            <li>• {t("pathA.what3")}</li>
            <li>• {t("pathA.what4")}</li>
            <li>• {t("pathA.what5")}</li>
          </ul>
          <h3 className="mt-6 text-sm font-semibold text-white">{t("pathA.processTitle")}</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-white/75">
            <li>{t("pathA.process1")}</li>
            <li>{t("pathA.process2")}</li>
            <li>{t("pathA.process3")}</li>
          </ol>
          <p className="mt-4 text-sm text-genesis-muted">{t("pathA.afterPay")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/order"
              className="inline-flex rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110"
            >
              {t("pathA.cta")} →
            </Link>
            <Link
              href="/order"
              className="inline-flex rounded-xl border border-emerald-500/40 px-5 py-3 text-sm font-medium text-emerald-100 hover:bg-emerald-950/40"
            >
              {t("pathA.ctaSecondary")}
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-black/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("pathA.faqTitle")}</h2>
          <dl className="mt-4 space-y-4 text-sm">
            <div>
              <dt className="font-medium text-white/90">{t("pathA.faq1q")}</dt>
              <dd className="mt-1 text-genesis-muted">{t("pathA.faq1a")}</dd>
            </div>
            <div>
              <dt className="font-medium text-white/90">{t("pathA.faq2q")}</dt>
              <dd className="mt-1 text-genesis-muted">{t("pathA.faq2a")}</dd>
            </div>
            <div>
              <dt className="font-medium text-white/90">{t("pathA.faq3q")}</dt>
              <dd className="mt-1 text-genesis-muted">
                {t("pathA.faq3a", { email: CONTACT_EMAIL })}{" "}
                <a
                  className="text-emerald-300 underline-offset-2 hover:underline"
                  href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("Support · Virtus Core Landing")}`}
                >
                  {CONTACT_EMAIL}
                </a>
              </dd>
            </div>
          </dl>
        </section>

        <p className="text-center text-xs text-genesis-muted">
          {t("pathA.foot", { brand: BRAND_NAME })}
        </p>
      </div>
    </PublicPageShell>
  );
}
