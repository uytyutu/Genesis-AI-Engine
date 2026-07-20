"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicApiBase } from "../lib/publicApiBase";
import { formatLocalizedMoney } from "../lib/formatEur";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { uiLangForMarket } from "../lib/marketLang";
import { filterPublicPackages } from "../lib/showSmokePackage";
import { PackagePreviewCarousel } from "../components/PackagePreviewCarousel";

type PackageCard = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
  currency?: string;
  price_label?: string;
};

type PublicReviews = {
  has_reviews: boolean;
  count: number;
  average_stars: number | null;
  recommend_pct: number | null;
  empty_message: string | null;
  reviews: {
    review_id?: string;
    stars: number;
    text: string;
    company_display_name?: string | null;
    verified_purchase?: boolean;
  }[];
};

const FALLBACK_PACKAGES: PackageCard[] = [
  {
    id: "basic",
    name: "Landing Basic",
    price_eur: 350,
    deliverables: [
      "Fertige moderne Landing Page (mobil) — Design nach Branche",
      "Ablauf, Zwischen-CTA und Trust-Leiste",
      "WhatsApp, Kontaktformular, Bewertungsblock",
      "Vollständiges Website-Archiv (ZIP) — Sie sind Eigentümer",
      "Anleitung zur Selbst-Veröffentlichung",
      "Rechtsvorlagen für Ihren Markt (von Ihnen zu prüfen)",
    ],
  },
  {
    id: "business",
    name: "Landing Business",
    price_eur: 650,
    deliverables: [
      "Alles aus Basic — plus Design für Kundengewinnung",
      "Google Maps mit Route, FAQ, Ablauf, Trust-Leiste",
      "Logo-Platzhalter und erweitertes SEO",
      "Hilfe beim Upload + 1 Korrekturrunde",
      "Hinweis: Domain- und Hosting-Gebühren zahlt der Kunde",
    ],
  },
  {
    id: "premium",
    name: "Landing Premium",
    price_eur: 1200,
    deliverables: [
      "Alles aus Business",
      "Exklusives Premium-Design, Showcase, Kennzahlen",
      "Kostenrechner und Analytics-Platzhalter",
      "Assisted Go-live bei Zugang + 14 Tage Support + 3 Korrekturen",
      "Kein Inhaber-Login / Online-Zahlung pro Warenkorb in diesem Paket",
      "Hinweis: Domain/Hosting-Miete nicht im Preis — nur Einrichtung",
    ],
  },
];

/**
 * Public Path A storefront — language follows ?market= (plus LanguageSwitcher).
 */
type MarketOption = {
  code: string;
  flag?: string;
  name_en?: string;
  basic_price_label?: string;
};

export function SitePage() {
  const { t, i18n } = useTranslation("site");
  const [packages, setPackages] = useState<PackageCard[]>(FALLBACK_PACKAGES);
  const [reviews, setReviews] = useState<PublicReviews | null>(null);
  const [market, setMarket] = useState("DE");
  const [markets, setMarkets] = useState<MarketOption[]>([]);

  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      const m = (p.get("market") || p.get("country") || "DE").toUpperCase();
      setMarket(m);
    } catch {
      setMarket("DE");
    }
  }, []);

  // ?market= drives storefront language (country ↔ currency ↔ package language)
  useEffect(() => {
    const lang = uiLangForMarket(market);
    const current = (i18n.language || "").slice(0, 2).toLowerCase();
    if (current !== lang) {
      void i18n.changeLanguage(lang);
    }
  }, [market, i18n]);

  useEffect(() => {
    const api = publicApiBase();
    const qs = `?market=${encodeURIComponent(market)}`;
    fetch(`${api}/api/sales/packages${qs}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        const list = body?.packages;
        if (Array.isArray(list) && list.length > 0) {
          setPackages(
            filterPublicPackages(
              list.map((p: PackageCard) => ({
                id: p.id,
                name: p.name,
                price_eur: p.price_eur,
                deliverables: Array.isArray(p.deliverables) ? p.deliverables : [],
                currency: p.currency,
                price_label: p.price_label,
              })),
            ),
          );
        }
      })
      .catch(() => {
        /* keep fallback — storefront must still render */
      });

    fetch(`${api}/api/public/pricing${qs}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        const rows = body?.markets;
        if (Array.isArray(rows) && rows.length > 0) {
          setMarkets(
            rows.map((m: MarketOption) => ({
              code: String(m.code || "").toUpperCase(),
              flag: m.flag,
              name_en: m.name_en,
              basic_price_label: m.basic_price_label,
            })),
          );
        }
      })
      .catch(() => undefined);
  }, [market]);

  useEffect(() => {
    const api = publicApiBase();
    const lang = (i18n.language || "de").slice(0, 2);
    fetch(`${api}/api/public/reviews?lang=${lang}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        if (body && typeof body === "object") setReviews(body as PublicReviews);
      })
      .catch(() => {
        /* honest empty via i18n if API down */
      });
  }, [i18n.language]);

  useEffect(() => {
    logCommerceEvent("tier_page_view", null, "site", { niche: null });
  }, [market]);

  const orderHref = `/order?market=${market}`;

  function orderHrefFor(pkg: string) {
    return `/order?market=${market}&package=${pkg}`;
  }

  function selectMarket(next: string) {
    const code = next.toUpperCase();
    setMarket(code);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("market", code);
      window.history.replaceState({}, "", url.toString());
    } catch {
      /* ignore */
    }
  }

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
          {markets.length > 0 ? (
            <div className="mx-auto max-w-md text-left">
              <label className="text-xs text-genesis-muted" htmlFor="site-market-select">
                Markt / Preise
              </label>
              <select
                id="site-market-select"
                className="mt-1 w-full rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-sm text-white"
                value={market}
                onChange={(e) => selectMarket(e.target.value)}
              >
                {markets.map((m) => (
                  <option key={m.code} value={m.code}>
                    {(m.flag ? `${m.flag} ` : "") +
                      (m.name_en || m.code) +
                      (m.basic_price_label ? ` · ab ${m.basic_price_label}` : "")}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
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
                <PackagePreviewCarousel packageId={p.id} className="mt-3" />
                <ul className="mt-3 space-y-1.5 text-xs text-white/70">
                  {p.deliverables.slice(0, 6).map((d) => (
                    <li key={d}>• {d}</li>
                  ))}
                </ul>
                <Link
                  href={orderHrefFor(p.id)}
                  onClick={() => logCommerceEvent("tier_select", p.id, "site")}
                  className="mt-4 inline-flex text-sm font-medium text-emerald-300 hover:underline"
                >
                  {t("pathA.cta")} →
                </Link>
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
              href={orderHref}
              onClick={() => logCommerceEvent("tier_select", null, "site")}
              className="inline-flex rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110"
            >
              {t("pathA.cta")} →
            </Link>
            <Link
              href={orderHref}
              onClick={() => logCommerceEvent("tier_select", null, "site")}
              className="inline-flex rounded-xl border border-emerald-500/40 px-5 py-3 text-sm font-medium text-emerald-100 hover:bg-emerald-950/40"
            >
              {t("pathA.ctaSecondary")}
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-black/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("reviews.title")}</h2>
          {!reviews?.has_reviews ? (
            <p className="mt-3 text-sm text-genesis-muted">
              {reviews?.empty_message || t("reviews.empty")}
            </p>
          ) : (
            <>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-emerald-100/90">
                {reviews.average_stars != null && (
                  <span className="rounded-lg border border-emerald-500/30 px-3 py-1.5">
                    ★ {t("reviews.avg", { avg: reviews.average_stars })}
                  </span>
                )}
                <span className="rounded-lg border border-emerald-500/30 px-3 py-1.5">
                  {t("reviews.count", { count: reviews.count })}
                </span>
                {reviews.recommend_pct != null && (
                  <span className="rounded-lg border border-emerald-500/30 px-3 py-1.5">
                    {t("reviews.recommend", { pct: reviews.recommend_pct })}
                  </span>
                )}
              </div>
              <ul className="mt-4 space-y-3">
                {reviews.reviews.map((r) => (
                  <li
                    key={r.review_id || r.text.slice(0, 24)}
                    className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm"
                  >
                    <p className="text-amber-300">{"★".repeat(Math.max(1, Math.min(5, r.stars)))}</p>
                    {(r.verified_purchase !== false) && (
                      <p className="mt-1 text-xs font-medium text-emerald-300/90">
                        ✔ {t("reviews.verifiedPurchase")}
                      </p>
                    )}
                    <p className="mt-2 text-white/85">«{r.text}»</p>
                    {r.company_display_name && (
                      <p className="mt-2 text-xs font-medium text-white/60">{r.company_display_name}</p>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
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
            <div>
              <dt className="font-medium text-white/90">{t("pathA.faq4q")}</dt>
              <dd className="mt-1 text-genesis-muted">{t("pathA.faq4a")}</dd>
            </div>
            <div>
              <dt className="font-medium text-white/90">{t("pathA.faq5q")}</dt>
              <dd className="mt-1 text-genesis-muted">
                {t("pathA.faq5a", { email: CONTACT_EMAIL })}
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
