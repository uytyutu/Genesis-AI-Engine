"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicApiBase } from "../lib/publicApiBase";
import { formatLocalizedMoney } from "../lib/formatEur";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { uiLangForMarket } from "../lib/marketLang";
import { filterPublicPackages } from "../lib/showSmokePackage";
import { PackagePreviewCarousel } from "../components/PackagePreviewCarousel";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { WebsiteAnalysisPanel } from "../components/WebsiteAnalysisPanel";
import { LANDING_PACKAGES_EUR } from "../lib/commercialCatalog";

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
    price_eur: LANDING_PACKAGES_EUR.basic,
    deliverables: [],
  },
  {
    id: "business",
    name: "Landing Business",
    price_eur: LANDING_PACKAGES_EUR.business,
    deliverables: [],
  },
  {
    id: "premium",
    name: "Landing Premium",
    price_eur: LANDING_PACKAGES_EUR.premium,
    deliverables: [],
  },
];

const PACKAGE_NAME_KEY: Record<string, string> = {
  basic: "pathA.pkgBasic",
  business: "pathA.pkgBusiness",
  premium: "pathA.pkgPremium",
};

const PACKAGE_DIFF_KEYS: Record<string, string[]> = {
  basic: ["pathA.diffBasic1", "pathA.diffBasic2", "pathA.diffBasic3"],
  business: ["pathA.diffBusiness1", "pathA.diffBusiness2", "pathA.diffBusiness3"],
  premium: ["pathA.diffPremium1", "pathA.diffPremium2", "pathA.diffPremium3"],
};

type MarketOption = {
  code: string;
  flag?: string;
  name_en?: string;
  basic_price_label?: string;
};

/**
 * S0 — Storefront First: buyable products first, Vector chat secondary.
 * Rule: Don't sell unfinished · 3 clicks to Order · prices locked 350/650/1200.
 */
export function SitePage() {
  const { t, i18n } = useTranslation("site");
  const [packages, setPackages] = useState<PackageCard[]>(FALLBACK_PACKAGES);
  const [reviews, setReviews] = useState<PublicReviews | null>(null);
  const [market, setMarket] = useState("DE");
  const [markets, setMarkets] = useState<MarketOption[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>("business");
  const localeTag = (i18n.language || "de").replace("_", "-");

  const openChat = useCallback(() => {
    setChatOpen(true);
    requestAnimationFrame(() => {
      document.getElementById("vector-chat-panel")?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    });
  }, []);

  function packageDiffLines(packageId: string): string[] {
    const keys = PACKAGE_DIFF_KEYS[packageId] || PACKAGE_DIFF_KEYS.basic!;
    return keys.map((k) => t(k));
  }

  function packageTitle(packageId: string, fallback: string): string {
    const key = PACKAGE_NAME_KEY[packageId];
    return key ? t(key) : fallback;
  }

  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      const m = (p.get("market") || p.get("country") || "DE").toUpperCase();
      setMarket(m);
      const view = (p.get("view") || "").toLowerCase();
      if (view === "vector" || window.location.hash.includes("vector")) {
        setChatOpen(true);
      }
    } catch {
      setMarket("DE");
    }
  }, []);

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
      .catch(() => undefined);

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
      .catch(() => undefined);
  }, [i18n.language]);

  useEffect(() => {
    logCommerceEvent("tier_page_view", null, "site", { niche: null });
  }, [market]);

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

  const comingSoon = t("s0.comingSoon", { defaultValue: "Coming Soon" });
  const orderLabel = t("pathA.cta");
  const detailsLabel = t("s0.details", { defaultValue: "Details" });

  return (
    <PublicPageShell>
      <div className="relative mx-auto max-w-4xl space-y-12 py-6 pb-28 animate-fade-up">
        {/* Hero — ecosystem, not chat */}
        <header className="space-y-4 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-300/90">
            {BRAND_NAME}
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t("s0.heroTitle", {
              defaultValue: "Digital ecosystem for business",
            })}
          </h1>
          <p className="mx-auto max-w-2xl text-base text-genesis-muted sm:text-lg">
            {t("s0.heroSubtitle", {
              defaultValue:
                "Websites, AI assistants, automation and analysis — clear packages, honest prices.",
              brand: BRAND_NAME,
            })}
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
          <p className="text-sm text-zinc-400">
            {t("s0.heroHint", {
              defaultValue: "Start with a website — ready to order today.",
            })}
          </p>
          <a
            href="#websites"
            className="inline-flex rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-black hover:brightness-110"
          >
            {t("s0.seeWebsites", { defaultValue: "See website packages" })} →
          </a>
        </header>

        {/* 1. Websites — primary commercial product */}
        <section id="websites" className="space-y-5" aria-labelledby="websites-heading">
          <div>
            <h2 id="websites-heading" className="text-2xl font-semibold text-white">
              {t("s0.websitesTitle", { defaultValue: "Websites" })}
            </h2>
            <p className="mt-1 text-sm text-genesis-muted">
              {t("pathA.packagesIntro")}
            </p>
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            {packages.map((p) => {
              const price =
                p.price_label ||
                formatLocalizedMoney(p.price_eur, p.currency || "EUR", localeTag);
              const diffs = packageDiffLines(p.id);
              const featured = p.id === "business";
              return (
                <article
                  key={p.id}
                  id={`pkg-${p.id}`}
                  className={`flex flex-col rounded-2xl border p-5 text-left ${
                    featured
                      ? "border-emerald-500/40 bg-emerald-950/25 shadow-[0_0_0_1px_rgba(16,185,129,0.15)]"
                      : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-zinc-300">
                      {packageTitle(p.id, p.name)}
                    </p>
                    {featured ? (
                      <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-200">
                        {t("s0.recommended", { defaultValue: "Recommended" })}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-3xl font-semibold text-white">{price}</p>
                  <ul className="mt-4 flex-1 space-y-2 text-sm text-zinc-300">
                    {diffs.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400" aria-hidden>
                          ✓
                        </span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <Link
                      href={orderHrefFor(p.id)}
                      onClick={() => logCommerceEvent("tier_select", p.id, "site")}
                      className="inline-flex flex-1 items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 min-w-[7rem]"
                    >
                      {orderLabel}
                    </Link>
                    <button
                      type="button"
                      onClick={() =>
                        setDetailId((cur) => (cur === p.id ? null : p.id))
                      }
                      className="inline-flex items-center justify-center rounded-xl border border-white/20 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/5"
                    >
                      {detailsLabel}
                    </button>
                  </div>
                  {detailId === p.id ? (
                    <div className="mt-4 border-t border-white/10 pt-4">
                      <PackagePreviewCarousel packageId={p.id} className="mt-1" />
                      <p className="mt-2 text-xs text-zinc-500">
                        {t("s0.previewHint", {
                          defaultValue: "Example look — order when ready.",
                        })}
                      </p>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        </section>

        {/* 2. AI Solutions */}
        <section className="space-y-4" aria-labelledby="ai-heading">
          <h2 id="ai-heading" className="text-2xl font-semibold text-white">
            {t("s0.aiTitle", { defaultValue: "AI Solutions" })}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <article className="rounded-2xl border border-sky-400/25 bg-sky-500/[0.07] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-200/90">
                {ASSISTANT_NAME}
              </p>
              <h3 className="mt-2 text-lg font-semibold text-white">
                {t("pathA.cardVectorTitle")}
              </h3>
              <p className="mt-2 text-sm text-zinc-300">
                {t("pathA.cardVectorBody")}
              </p>
              <p className="mt-3 text-sm text-zinc-400">
                {t("s0.vectorAsk", {
                  defaultValue: "Not sure what fits? Ask Vector.",
                })}
              </p>
              <button
                type="button"
                onClick={openChat}
                className="mt-4 inline-flex rounded-xl border border-sky-400/40 px-4 py-2 text-sm font-medium text-sky-100 hover:bg-sky-500/10"
              >
                {t("pathA.meetVectorCta")}
              </button>
            </article>
            <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
              <h3 className="text-lg font-semibold text-white">
                {t("pathA.cardChatbotTitle")}
              </h3>
              <p className="mt-2 text-sm text-zinc-400">
                {t("pathA.cardChatbotBody")}
              </p>
              <p className="mt-2 text-xs text-zinc-500">
                Instagram · Facebook · WhatsApp · Telegram · Website
              </p>
              <span className="mt-4 inline-flex rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-1.5 text-xs font-semibold text-amber-100/90">
                {comingSoon}
              </span>
            </article>
          </div>
        </section>

        {/* 3. Automation */}
        <section className="space-y-4" aria-labelledby="auto-heading">
          <h2 id="auto-heading" className="text-2xl font-semibold text-white">
            {t("s0.automationTitle", { defaultValue: "Automation & CRM" })}
          </h2>
          <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <h3 className="text-lg font-semibold text-white">
              {t("pathA.cardAutomationTitle")}
            </h3>
            <p className="mt-2 text-sm text-zinc-400">
              {t("pathA.cardAutomationBody")}
            </p>
            <p className="mt-2 text-xs text-zinc-500">CRM · Email · Leads · Workflows</p>
            <span className="mt-4 inline-flex rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-1.5 text-xs font-semibold text-amber-100/90">
              {comingSoon}
            </span>
          </article>
        </section>

        {/* 4. Analysis — Website Analysis v1 */}
        <section className="space-y-4" aria-labelledby="analysis-heading" id="analysis">
          <h2 id="analysis-heading" className="text-2xl font-semibold text-white">
            {t("s0.analysisTitle", { defaultValue: "Business Analysis" })}
          </h2>
          <WebsiteAnalysisPanel market={market} onAskVector={openChat} />
        </section>

        {/* 5. One-time — Repair is sold via Analysis funnel, not a hero card */}
        <section className="space-y-4" aria-labelledby="onetime-heading">
          <h2 id="onetime-heading" className="text-2xl font-semibold text-white">
            {t("s0.onetimeTitle", { defaultValue: "One-time services" })}
          </h2>
          <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm text-zinc-400">
              Website Repair появляется после бесплатного анализа выше — только если
              ремонт выгоднее нового сайта. Migration · Google Business · SEO Fixes —
              отдельно.
            </p>
            <a
              href="#analysis"
              className="mt-4 inline-flex rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-3 py-1.5 text-xs font-semibold text-emerald-100/90 hover:brightness-110"
            >
              Сначала анализ →
            </a>
            <p className="mt-3 text-xs text-zinc-500">
              {t("s0.honestNote", {
                defaultValue: "Coming Soon is not Buy — we only sell finished delivery paths.",
              })}
            </p>
          </article>
        </section>

        {/* Process + trust (below fold) */}
        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("pathA.whatTitle")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• {t("pathA.what1")}</li>
            <li>• {t("pathA.what2")}</li>
            <li>• {t("pathA.what3")}</li>
            <li>• {t("pathA.what5")}</li>
          </ul>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <Link href="/products" className="font-medium text-emerald-300 hover:underline">
              {t("pathA.productsLink")} →
            </Link>
            <Link href="/client/login" className="font-medium text-zinc-300 hover:underline">
              {t("pathA.cabinetLink")} →
            </Link>
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="font-medium text-zinc-400 hover:underline"
            >
              {CONTACT_EMAIL}
            </a>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-black/20 p-6">
          <h2 className="text-lg font-semibold text-white">{t("reviews.title")}</h2>
          {!reviews?.has_reviews ? (
            <p className="mt-3 text-sm text-genesis-muted">
              {reviews?.empty_message || t("reviews.empty")}
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {reviews.reviews.slice(0, 3).map((r) => (
                <li
                  key={r.review_id || r.text.slice(0, 24)}
                  className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm"
                >
                  <p className="text-amber-300">
                    {"★".repeat(Math.max(1, Math.min(5, r.stars)))}
                  </p>
                  <p className="mt-2 text-white/85">«{r.text}»</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <p className="text-center text-xs text-white/40">
          {t("pathA.foot", { brand: BRAND_NAME })}
        </p>

        {/* Secondary Vector chat panel — wide consultant surface, not a tiny widget */}
        {chatOpen ? (
          <div
            id="vector-chat-panel"
            className="fixed inset-x-2 bottom-20 top-16 z-40 mx-auto flex w-auto max-w-3xl flex-col overflow-hidden rounded-2xl border border-sky-400/30 bg-genesis-bg shadow-2xl sm:inset-x-auto sm:right-6 sm:left-auto sm:top-auto sm:bottom-20 sm:h-[min(78vh,720px)] sm:w-[min(720px,calc(100vw-3rem))]"
          >
            <div className="flex shrink-0 items-center justify-between border-b border-white/10 px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-white">
                  {ASSISTANT_NAME}
                </p>
                <p className="text-xs text-zinc-400">
                  {t("s0.chatHint", {
                    defaultValue: "Consultant — helps you choose a package",
                  })}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen(false)}
                className="rounded-lg px-2 py-1 text-sm text-zinc-400 hover:bg-white/5 hover:text-white"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-2">
              <GenesisConcierge scope="public" />
            </div>
          </div>
        ) : null}

        {/* Floating ask Vector */}
        <button
          type="button"
          onClick={() => (chatOpen ? setChatOpen(false) : openChat())}
          className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-sky-400/40 bg-sky-600 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:brightness-110"
        >
          {chatOpen
            ? t("s0.closeChat", { defaultValue: "Close" })
            : t("s0.askVector", { defaultValue: "Ask Vector" })}
        </button>
      </div>
    </PublicPageShell>
  );
}
