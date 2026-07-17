"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicApiBase } from "../lib/publicApiBase";
import { formatLocalizedMoney } from "../lib/formatEur";

type PackageCard = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
  currency?: string;
  price_label?: string;
};

const FALLBACK_PACKAGES: PackageCard[] = [
  {
    id: "basic",
    name: "Landing Basic",
    price_eur: 350,
    deliverables: [
      "Moderne One-Page-Website",
      "Responsive für Smartphone, Tablet und Desktop",
      "Basis-SEO",
      "Kontakte und Anfrageformular",
      "WhatsApp-Button",
    ],
  },
  {
    id: "business",
    name: "Landing Business",
    price_eur: 650,
    deliverables: [
      "Alles aus Basic",
      "Google Maps",
      "Bewertungsblock",
      "Logo im Layout (bestehendes Kundenlogo)",
      "Erweitertes SEO",
      "1 Korrekturrunde",
    ],
  },
  {
    id: "premium",
    name: "Landing Premium",
    price_eur: 1200,
    deliverables: [
      "Alles aus Business",
      "Premium-Design",
      "Google Analytics Einrichtung",
      "Hilfe bei Domain-Auswahl, Kauf und Einrichtung",
      "Termin-/Anfrageformular oder Rechner",
      "14 Tage Support nach dem Launch",
      "3 Korrekturrunden",
      "Prioritäts-Support",
    ],
  },
];

/**
 * Public Path A storefront — DE-first via i18n (browser locale + LanguageSwitcher).
 */
export function SitePage() {
  const { t } = useTranslation("site");
  const [packages, setPackages] = useState<PackageCard[]>(FALLBACK_PACKAGES);

  useEffect(() => {
    const api = publicApiBase();
    fetch(`${api}/api/sales/packages`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        const list = body?.packages;
        if (Array.isArray(list) && list.length > 0) {
          setPackages(
            list.map((p: PackageCard) => ({
              id: p.id,
              name: p.name,
              price_eur: p.price_eur,
              deliverables: Array.isArray(p.deliverables) ? p.deliverables : [],
              currency: p.currency,
              price_label: p.price_label,
            })),
          );
        }
      })
      .catch(() => {
        /* keep fallback — storefront must still render */
      });
  }, []);

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
          {packages.map((p) => {
            const price =
              p.price_label ||
              formatLocalizedMoney(p.price_eur, p.currency || "EUR", "de-DE");
            return (
              <div
                key={p.id}
                className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left"
              >
                <p className="text-sm text-genesis-muted">{p.name}</p>
                <p className="mt-1 text-2xl font-semibold text-white">{price}</p>
                <ul className="mt-3 space-y-1.5 text-xs text-white/70">
                  {p.deliverables.slice(0, 6).map((d) => (
                    <li key={d}>• {d}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </section>

        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("pathA.whatTitle")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• {t("pathA.what1")}</li>
            <li>• {t("pathA.what2")}</li>
            <li>• {t("pathA.what3")}</li>
            <li>• {t("pathA.whatLogo")}</li>
            <li>• {t("pathA.what4")}</li>
            <li>• {t("pathA.whatDomain")}</li>
            <li>• {t("pathA.whatLegal")}</li>
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
                {t("pathA.faq3a", { email: CONTACT_EMAIL })}
              </dd>
            </div>
          </dl>
        </section>

        <p className="text-center text-xs text-white/40">
          {t("pathA.foot", { brand: BRAND_NAME })}
        </p>
      </div>
    </PublicPageShell>
  );
}
