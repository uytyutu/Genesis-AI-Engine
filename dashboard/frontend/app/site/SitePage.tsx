"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useTransition,
} from "react";
import { useTranslation } from "react-i18next";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicApiBase } from "../lib/publicApiBase";
import { formatLocalizedMoney } from "../lib/formatEur";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { canonicalMarketForLang } from "../lib/marketLang";
import { filterPublicPackages } from "../lib/showSmokePackage";
import { LANDING_PACKAGES_EUR } from "../lib/commercialCatalog";
import { CommercialAgencyHub } from "../components/storefront/CommercialAgencyHub";
import { CHATBOT_PRICE_TIERS } from "../components/storefront/modules";
import {
  agencyCardSurface,
} from "../lib/agencySelectionStyles";
import { VectorAvatarStage, VectorChatIcon } from "../components/VectorAvatar";
import { useLocale } from "../context/LocaleContext";
import type { UiLocale } from "../lib/locale/types";

const PackagePreviewCarousel = dynamic(
  () =>
    import("../components/PackagePreviewCarousel").then((m) => m.PackagePreviewCarousel),
  { ssr: false, loading: () => null },
);
const WebsiteAnalysisPanel = dynamic(
  () =>
    import("../components/WebsiteAnalysisPanel").then((m) => m.WebsiteAnalysisPanel),
  { ssr: false, loading: () => (
    <p className="text-sm text-zinc-500">Laden…</p>
  ) },
);
const GenesisConcierge = dynamic(
  () => import("../components/GenesisConcierge").then((m) => m.GenesisConcierge),
  { ssr: false, loading: () => null },
);

type PackageCard = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
  currency?: string;
  price_label?: string;
};

type BotPackageCard = {
  package_id: string;
  name: string;
  setup_label: string;
  monthly_label: string;
  price_label: string;
  tagline_ru?: string;
  includes_ru?: string[];
  features?: {
    knowledge_sources?: string;
    languages?: string;
    scenarios?: string;
    ai_analysis?: boolean;
    training?: string;
    extra_channels?: string;
    support?: string;
  };
};

type ServiceView = "hub" | "websites" | "bots" | "analysis";

type PublicReviews = {
  has_reviews: boolean;
  count: number;
  average_stars: number | null;
  recommend_pct: number | null;
  empty_message?: string | null;
  reviews: {
    review_id?: string;
    stars: number;
    text: string;
    company_display_name?: string | null;
    service_label?: string | null;
    service_kind?: string | null;
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
  const { uiLocale } = useLocale();
  const router = useRouter();
  const [, startViewTransition] = useTransition();
  const syncLock = useRef<"market" | "lang" | null>(null);
  const [packages, setPackages] = useState<PackageCard[]>(FALLBACK_PACKAGES);
  const [reviews, setReviews] = useState<PublicReviews | null>(null);
  const [market, setMarket] = useState("DE");
  const [markets, setMarkets] = useState<MarketOption[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [vvLayout, setVvLayout] = useState<{ height: number; offsetTop: number; keyboard: number }>({
    height: 0,
    offsetTop: 0,
    keyboard: 0,
  });
  const [detailId, setDetailId] = useState<string | null>("business");
  const [selectedPackageId, setSelectedPackageId] = useState("business");
  const [analyzeUrl, setAnalyzeUrl] = useState("");
  const [serviceView, setServiceView] = useState<ServiceView>("hub");
  const [botPackages, setBotPackages] = useState<BotPackageCard[]>([]);
  const localeTag = (i18n.language || "de").replace("_", "-");
  const CHAT_POS_KEY = "vector-chat-panel-pos";

  function writeServiceToUrl(view: ServiceView) {
    try {
      const url = new URL(window.location.href);
      if (view === "hub") {
        url.searchParams.delete("service");
        url.hash = "";
      } else {
        url.searchParams.set("service", view);
        url.hash = view;
      }
      window.history.replaceState({}, "", url.toString());
    } catch {
      /* ignore */
    }
  }

  function openService(view: ServiceView) {
    startViewTransition(() => {
      setServiceView(view);
    });
    writeServiceToUrl(view);
    if (view === "websites" || view === "bots" || view === "analysis") {
      try {
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch {
        /* ignore */
      }
    }
  }

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const a = (params.get("analyze") || params.get("url") || "").trim();
      if (a) {
        setAnalyzeUrl(a);
        setServiceView("analysis");
        writeServiceToUrl("analysis");
        return;
      }
      const service = (params.get("service") || "").toLowerCase();
      const hash = (window.location.hash || "").replace(/^#/, "").toLowerCase();
      const raw = service || hash;
      if (raw === "websites" || raw === "bots" || raw === "analysis") {
        setServiceView(raw);
      } else {
        setServiceView("hub");
      }
      const pkg = (params.get("package") || "").toLowerCase();
      if (pkg === "basic" || pkg === "business" || pkg === "premium") {
        setSelectedPackageId(pkg);
        setDetailId(pkg);
      }
    } catch {
      /* ignore */
    }
    const onPop = () => {
      try {
        const params = new URLSearchParams(window.location.search);
        const service = (params.get("service") || "").toLowerCase();
        if (service === "websites" || service === "bots" || service === "analysis") {
          setServiceView(service);
        } else if (!service) {
          setServiceView("hub");
        }
      } catch {
        /* ignore */
      }
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    // Clear legacy free-drag coordinates — Vector stays docked bottom-right while browsing.
    try {
      sessionStorage.removeItem(CHAT_POS_KEY);
    } catch {
      /* ignore */
    }
  }, [CHAT_POS_KEY]);

  useEffect(() => {
    if (typeof window === "undefined" || !window.visualViewport) return;
    const vv = window.visualViewport;
    const sync = () => {
      const keyboard = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
      setVvLayout({ height: vv.height, offsetTop: vv.offsetTop, keyboard });
    };
    sync();
    vv.addEventListener("resize", sync);
    vv.addEventListener("scroll", sync);
    return () => {
      vv.removeEventListener("resize", sync);
      vv.removeEventListener("scroll", sync);
    };
  }, []);

  const openChat = useCallback(() => {
    setChatOpen(true);
  }, []);

  function packageDiffLines(packageId: string): string[] {
    const keys = PACKAGE_DIFF_KEYS[packageId] || PACKAGE_DIFF_KEYS.basic!;
    return keys.map((k) => t(k));
  }

  function packageTitle(packageId: string, fallback: string): string {
    const key = PACKAGE_NAME_KEY[packageId];
    return key ? t(key) : fallback;
  }

  function writeMarketToUrl(code: string) {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("market", code);
      window.history.replaceState({}, "", url.toString());
    } catch {
      /* ignore */
    }
  }

  function selectMarket(next: string) {
    const code = next.toUpperCase();
    syncLock.current = "market";
    setMarket(code);
    writeMarketToUrl(code);
    // L0: market = prices/currency/legal only — never override uiLocale
  }

  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      const explicit = (p.get("market") || p.get("country") || "").toUpperCase();
      if (explicit) {
        // Explicit price-policy URL → market only (language stays uiLocale SSOT).
        syncLock.current = "market";
        setMarket(explicit);
      } else {
        // LanguageSwitcher / localStorage wins → sync market + URL to UI language.
        const next = canonicalMarketForLang(uiLocale);
        syncLock.current = "lang";
        setMarket(next);
        writeMarketToUrl(next);
      }
      const view = (p.get("view") || "").toLowerCase();
      if (view === "vector" || window.location.hash.includes("vector")) {
        setChatOpen(true);
      }
    } catch {
      setMarket(canonicalMarketForLang(uiLocale));
    }
    // Initial URL ↔ market only once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // LanguageSwitcher is source of truth when buyer picks a UI language → suggest market.
  useEffect(() => {
    if (syncLock.current === "market") {
      syncLock.current = null;
      return;
    }
    const next = canonicalMarketForLang(uiLocale);
    if (next === market) return;
    syncLock.current = "lang";
    setMarket(next);
    writeMarketToUrl(next);
  }, [uiLocale, market]);

  useEffect(() => {
    const api = publicApiBase();
    const qs = `?market=${encodeURIComponent(market)}`;
    let cancelled = false;

    const loadPackagesAndMarkets = () => {
      if (cancelled) return;
      fetch(`${api}/api/sales/packages${qs}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((body) => {
          if (cancelled) return;
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
          if (cancelled) return;
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
    };

    const loadBots = () => {
      if (cancelled) return;
      fetch(`${api}/api/public/bots/pricing${qs}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((body) => {
          if (cancelled) return;
          const list = body?.packages;
          if (Array.isArray(list) && list.length > 0) {
            setBotPackages(
              list.map((p: BotPackageCard) => ({
                package_id: String(p.package_id || ""),
                name: String(p.name || ""),
                setup_label: String(p.setup_label || ""),
                monthly_label: String(p.monthly_label || ""),
                price_label: String(p.price_label || ""),
                tagline_ru: p.tagline_ru ? String(p.tagline_ru) : undefined,
                includes_ru: Array.isArray(p.includes_ru)
                  ? p.includes_ru.map(String)
                  : undefined,
                features: p.features,
              })),
            );
          }
        })
        .catch(() => undefined);
    };

    // Defer network so first paint / clicks are not blocked. setTimeout avoids
    // Window.requestIdleCallback TS narrowing that broke Vercel builds.
    const hubTimer = window.setTimeout(loadPackagesAndMarkets, 0);
    const botsTimer = window.setTimeout(loadBots, 500);

    return () => {
      cancelled = true;
      window.clearTimeout(hubTimer);
      window.clearTimeout(botsTimer);
    };
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

  // Warm order routes so card clicks feel instant.
  useEffect(() => {
    router.prefetch("/order");
    router.prefetch("/order/bot");
    router.prefetch("/order/service/website_repair");
    router.prefetch("/order/service/ai_website_analysis");
  }, [router]);

  function orderHrefFor(pkg: string) {
    return `/order?market=${encodeURIComponent(market)}&package=${encodeURIComponent(pkg)}&form=1`;
  }

  function selectWebsitePackage(id: string) {
    setSelectedPackageId(id);
    setDetailId(id);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("package", id);
      window.history.replaceState({}, "", url.toString());
    } catch {
      /* ignore */
    }
  }

  const comingSoon = t("s0.comingSoon", { defaultValue: "Coming Soon" });
  const orderLabel = t("pathA.cta");
  const detailsLabel = t("s0.details", { defaultValue: "Details" });
  const backLabel = t("s0.backToServices", { defaultValue: "← All services" });
  const botOrderHref = (packageId: string) =>
    `/order/bot?market=${encodeURIComponent(market)}&package=${encodeURIComponent(packageId)}`;

  const marketSelect =
    markets.length > 0 ? (
      <div className="mx-auto max-w-md text-left">
        <label className="text-xs text-genesis-muted" htmlFor="site-market-select">
          {t("s0.marketLabel", { defaultValue: "Market / prices" })}
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
                (m.basic_price_label
                  ? ` · ${t("s0.priceFrom", { defaultValue: "from" })} ${m.basic_price_label}`
                  : "")}
            </option>
          ))}
        </select>
      </div>
    ) : null;

  return (
    <PublicPageShell>
      <div
        className={`storefront-page relative z-[1] mx-auto space-y-12 py-6 pb-28 ${
          serviceView === "hub" ? "max-w-7xl" : "max-w-4xl"
        }`}
      >
        {serviceView === "hub" ? (
          <CommercialAgencyHub
            market={market}
            localeTag={localeTag}
            marketSelect={marketSelect}
            reviews={reviews}
            botPackages={botPackages}
            onOpenWebsites={() => openService("websites")}
            onOpenBots={() => openService("bots")}
            onOpenAnalysis={() => openService("analysis")}
            orderHrefFor={orderHrefFor}
            botOrderHrefFor={botOrderHref}
          />
        ) : null}

        {serviceView === "websites" ? (
          <section id="websites" className="space-y-5" aria-labelledby="websites-heading">
            <button
              type="button"
              onClick={() => openService("hub")}
              className="platform-link"
            >
              {backLabel}
            </button>
            <div>
              <h2 id="websites-heading" className="text-2xl font-semibold text-white">
                {t("s0.websitesTitle", { defaultValue: "Websites" })}
              </h2>
              <p className="mt-1 text-sm text-genesis-muted">
                {t("pathA.packagesIntro")}
              </p>
            </div>
            {marketSelect}
            {selectedPackageId ? (
              <div
                className={`rounded-2xl border p-4 ${agencyCardSurface(true)}`}
                role="status"
                aria-live="polite"
              >
                <p className="text-lg font-semibold text-white">
                  {t("agencyHub.products.selectedLine", {
                    defaultValue: "✓ Website — {{tier}} ausgewählt",
                    tier: packageTitle(
                      selectedPackageId,
                      selectedPackageId,
                    ),
                  })}
                </p>
                <p className="mt-1 text-sm text-violet-200/90">
                  {formatLocalizedMoney(
                    packages.find((p) => p.id === selectedPackageId)?.price_eur ??
                      LANDING_PACKAGES_EUR[
                        selectedPackageId as keyof typeof LANDING_PACKAGES_EUR
                      ] ??
                      LANDING_PACKAGES_EUR.business,
                    "EUR",
                    localeTag,
                  )}
                </p>
              </div>
            ) : null}
            <div className="grid gap-4 lg:grid-cols-3">
              {packages.map((p) => {
                const price =
                  p.price_label ||
                  formatLocalizedMoney(p.price_eur, p.currency || "EUR", localeTag);
                const diffs = packageDiffLines(p.id);
                const featured = p.id === "business";
                const isSelected = selectedPackageId === p.id;
                return (
                  <article
                    key={p.id}
                    id={`pkg-${p.id}`}
                    role="button"
                    tabIndex={0}
                    onClick={() => selectWebsitePackage(p.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") selectWebsitePackage(p.id);
                    }}
                    className={`flex cursor-pointer flex-col rounded-2xl border p-5 text-left transition ${agencyCardSurface(
                      isSelected,
                      featured && !isSelected,
                    )}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-zinc-300">
                        {packageTitle(p.id, p.name)}
                      </p>
                      {isSelected ? (
                        <span className="inline-flex items-center gap-1 rounded-full border border-violet-400/50 bg-violet-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-violet-100">
                          <span aria-hidden>✓</span>
                          {t("agencyHub.products.selected", {
                            defaultValue: "Ausgewählt",
                          })}
                        </span>
                      ) : featured ? (
                        <span className="platform-badge">
                          {t("s0.recommended", { defaultValue: "Recommended" })}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-3xl font-semibold text-white">{price}</p>
                    <ul className="mt-4 flex-1 space-y-2 text-sm text-zinc-300">
                      {diffs.map((d) => (
                        <li key={d} className="flex gap-2">
                          <span className="platform-check" aria-hidden>
                            ✓
                          </span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-5 flex flex-wrap gap-2">
                      <Link
                        href={orderHrefFor(p.id)}
                        onClick={(e) => {
                          e.stopPropagation();
                          logCommerceEvent("tier_select", p.id, "site");
                        }}
                        className={`flex-1 min-w-[7rem] inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition ${
                          isSelected
                            ? "bg-violet-600 shadow-[0_12px_40px_-12px_rgba(124,58,237,0.9)] hover:bg-violet-500"
                            : "platform-btn-primary"
                        }`}
                      >
                        {orderLabel}
                      </Link>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDetailId((cur) => (cur === p.id ? null : p.id));
                        }}
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
            <p className="text-sm text-zinc-400">
              {t("s0.needAccount", {
                defaultValue: "Want an office to manage this later?",
              })}{" "}
              <Link href="/client/register" className="platform-link">
                {t("s0.createAccount", { defaultValue: "Create personal account" })}
              </Link>
            </p>
          </section>
        ) : null}

        {serviceView === "bots" ? (
          <section id="bots" className="space-y-5" aria-labelledby="bots-heading">
            <button
              type="button"
              onClick={() => openService("hub")}
              className="platform-link"
            >
              {backLabel}
            </button>
            <div>
              <h2 id="bots-heading" className="text-2xl font-semibold text-white">
                {t("s0.botsTitle", { defaultValue: "AI Digital Employee" })}
              </h2>
              <p className="mt-1 text-sm text-genesis-muted">
                {t("s0.botsIntro", {
                  defaultValue:
                    "A digital employee with onboarding: answers clients, captures leads, books services. You pay for outcomes — not a messenger logo list.",
                })}
              </p>
            </div>
            {marketSelect}
            <div className="grid gap-4 sm:grid-cols-3">
              {botPackages.length === 0 ? (
                <p className="text-sm text-zinc-500 sm:col-span-3">
                  {t("s0.botsLoading", { defaultValue: "Loading bot packages…" })}
                </p>
              ) : (
                botPackages.map((pkg) => {
                  const tier = CHATBOT_PRICE_TIERS.find((x) => x.id === pkg.package_id);
                  const isRu = (i18n.language || "").startsWith("ru");
                  return (
                  <article
                    key={pkg.package_id}
                    className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
                  >
                    <p className="text-lg font-semibold text-white">{pkg.name}</p>
                    <p className="platform-price mt-3">
                      {pkg.setup_label || pkg.price_label}
                    </p>
                    {pkg.monthly_label ? (
                      <p className="mt-1 text-sm text-zinc-400">
                        {t("s0.botsMonthly", {
                          defaultValue: "setup · then {{monthly}}/mo",
                          monthly: pkg.monthly_label,
                        })}
                      </p>
                    ) : null}
                    {pkg.tagline_ru && isRu ? (
                      <p className="mt-3 text-sm leading-relaxed text-zinc-300">{pkg.tagline_ru}</p>
                    ) : tier?.blurbKey ? (
                      <p className="mt-3 text-sm leading-relaxed text-zinc-300">
                        {t(`appStore.${tier.blurbKey}`, {
                          defaultValue: "",
                        })}
                      </p>
                    ) : null}
                    <ul className="mt-3 flex-1 space-y-1.5 text-xs leading-relaxed text-zinc-400">
                      {isRu && pkg.includes_ru?.length
                        ? pkg.includes_ru.slice(0, 5).map((line) => (
                            <li key={line} className="flex gap-2">
                              <span className="platform-check" aria-hidden>
                                ✓
                              </span>
                              <span>{line}</span>
                            </li>
                          ))
                        : (tier?.outcomeKeys ?? []).map((key) => (
                            <li key={key} className="flex gap-2">
                              <span className="platform-check" aria-hidden>
                                ✓
                              </span>
                              <span>{t(`appStore.${key}`)}</span>
                            </li>
                          ))}
                    </ul>
                    <p className="mt-3 text-[11px] text-zinc-600">
                      {t("s0.botsChannelsNote", {
                        defaultValue:
                          "Live now: Telegram + Website Chat. WhatsApp / Instagram / Messenger — coming soon (not sold as ready).",
                      })}
                    </p>
                    <Link
                      href={botOrderHref(pkg.package_id)}
                      className="platform-btn-primary mt-5"
                    >
                      {t("s0.botsCta", {
                        defaultValue: "Choose package →",
                      })}
                    </Link>
                  </article>
                  );
                })
              )}
            </div>
          </section>
        ) : null}

        {serviceView === "analysis" ? (
          <section
            id="analysis"
            className="space-y-4"
            aria-labelledby="analysis-heading"
          >
            <button
              type="button"
              onClick={() => openService("hub")}
              className="platform-link"
            >
              {backLabel}
            </button>
            <h2 id="analysis-heading" className="text-2xl font-semibold text-white">
              {t("s0.analysisTitle", { defaultValue: "Website Analysis & Repair" })}
            </h2>
            <WebsiteAnalysisPanel
              market={market}
              onAskVector={openChat}
              initialUrl={analyzeUrl || undefined}
            />
            <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white sm:text-lg">
                {t("s0.repairMvpTitle")}
              </h3>
              <p className="mt-2 text-sm text-zinc-400">{t("s0.repairMvpIntro")}</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="platform-eyebrow-sm">
                    {t("s0.repairMvpFindTitle")}
                  </p>
                  <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
                    <li>{t("s0.repairMvpFind1")}</li>
                    <li>{t("s0.repairMvpFind2")}</li>
                    <li>{t("s0.repairMvpFind3")}</li>
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-sky-300/90">
                    {t("s0.repairMvpFixTitle")}
                  </p>
                  <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
                    <li>{t("s0.repairMvpFix1")}</li>
                    <li>{t("s0.repairMvpFix2")}</li>
                    <li>{t("s0.repairMvpFix3")}</li>
                  </ul>
                </div>
              </div>
              <p className="mt-4 text-xs leading-relaxed text-zinc-500">
                {t("s0.repairMvpDisclaimer")}
              </p>
            </article>
          </section>
        ) : null}

        {/* Process + trust (below fold on product views; hub has its own story) */}
        {serviceView !== "hub" ? (
        <section className="platform-panel p-6">
          <h2 className="text-lg font-semibold text-white">{t("pathA.whatTitle")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• {t("pathA.what1")}</li>
            <li>• {t("pathA.what2")}</li>
            <li>• {t("pathA.what3")}</li>
            <li>• {t("pathA.what5")}</li>
          </ul>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <Link href="/products" className="platform-link">
              {t("pathA.productsLink")} →
            </Link>
            <Link href="/client/register" className="platform-link">
              {t("s0.createAccount", { defaultValue: "Create personal account" })} →
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
        ) : null}

        {serviceView !== "hub" ? (
        <p className="text-center text-xs text-white/40">
          {t("pathA.foot", { brand: BRAND_NAME })}
        </p>
        ) : null}

        {/* Vector chat — docked ChatGPT-like panel + MP4 (stays while browsing) */}
        {chatOpen ? (
          <div
            id="vector-chat-panel"
            style={
              vvLayout.height
                ? {
                    maxHeight: `${Math.max(320, vvLayout.height - 16)}px`,
                  }
                : undefined
            }
            className="vector-chat-panel fixed inset-0 z-[60] flex h-dvh max-h-dvh w-full flex-col overflow-hidden border-0 sm:inset-auto sm:bottom-4 sm:right-4 sm:left-auto sm:h-[min(88dvh,820px)] sm:max-h-[min(88dvh,820px)] sm:w-[min(980px,calc(100vw-1.5rem))] sm:rounded-3xl sm:border sm:border-white/10"
          >
            <div className="vector-chat-panel__bg" aria-hidden>
              <div className="vector-chat-panel__mesh" />
              <div className="vector-chat-panel__orb vector-chat-panel__orb--a" />
              <div className="vector-chat-panel__orb vector-chat-panel__orb--b" />
              <div className="vector-chat-panel__noise" />
            </div>
            <div className="vector-chat-panel__content">
            <div className="flex shrink-0 items-center justify-between gap-2 border-b border-white/10 bg-black/25 px-3 py-2.5 backdrop-blur-md sm:px-4">
              <div className="flex min-w-0 items-center gap-3">
                <button
                  type="button"
                  className="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-300 transition hover:bg-white/8 hover:text-white md:hidden"
                  aria-label="История чатов"
                  onClick={() => {
                    window.dispatchEvent(new Event("genesis:toggle-history"));
                  }}
                >
                  ☰
                </button>
                <VectorChatIcon size="sm" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">
                    {ASSISTANT_NAME}
                  </p>
                  <p className="truncate text-[11px] text-sky-200/70">
                    {t("s0.chatHint", {
                      defaultValue: "Berater · Produkte & Pakete",
                    })}
                  </p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    window.dispatchEvent(new Event("genesis:new-chat"));
                  }}
                  className="rounded-xl px-2.5 py-2 text-xs font-semibold text-zinc-200 hover:bg-white/8"
                  aria-label={t("s0.newChat", { defaultValue: "New chat" })}
                >
                  {t("s0.newChat", { defaultValue: "New" })}
                </button>
                <button
                  type="button"
                  onClick={() => setChatOpen(false)}
                  className="rounded-xl px-2.5 py-2 text-sm text-zinc-400 hover:bg-white/8 hover:text-white"
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="flex min-h-0 flex-1 overflow-hidden">
              <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden [&_#genesis-chat]:h-full [&_#genesis-chat]:max-h-none [&_#genesis-chat]:min-h-0 [&_#genesis-chat]:rounded-none [&_#genesis-chat]:border-0 [&_#genesis-chat]:bg-transparent [&_#genesis-chat]:shadow-none">
                <GenesisConcierge scope="public" />
              </div>
              <VectorAvatarStage className="hidden w-[min(15rem,28%)] lg:flex" />
            </div>
            </div>
          </div>
        ) : null}

        {/* Public storefront: no Vector FAB — matches live beta /site */}
      </div>
    </PublicPageShell>
  );
}
