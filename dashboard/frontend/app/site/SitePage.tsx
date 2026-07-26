"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicApiBase } from "../lib/publicApiBase";
import { formatLocalizedMoney } from "../lib/formatEur";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { canonicalMarketForLang, uiLangForMarket } from "../lib/marketLang";
import { filterPublicPackages } from "../lib/showSmokePackage";
import { PackagePreviewCarousel } from "../components/PackagePreviewCarousel";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { WebsiteAnalysisPanel } from "../components/WebsiteAnalysisPanel";
import { LANDING_PACKAGES_EUR } from "../lib/commercialCatalog";
import { useLocale } from "../context/LocaleContext";
import type { UiLocale } from "../lib/locale/types";

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
  const { uiLocale, applyUiLocale } = useLocale();
  const syncLock = useRef<"market" | "lang" | null>(null);
  const [packages, setPackages] = useState<PackageCard[]>(FALLBACK_PACKAGES);
  const [reviews, setReviews] = useState<PublicReviews | null>(null);
  const [market, setMarket] = useState("DE");
  const [markets, setMarkets] = useState<MarketOption[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatPos, setChatPos] = useState<{ x: number; y: number } | null>(null);
  const [vvLayout, setVvLayout] = useState<{ height: number; offsetTop: number; keyboard: number }>({
    height: 0,
    offsetTop: 0,
    keyboard: 0,
  });
  const chatDragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);
  const [detailId, setDetailId] = useState<string | null>("business");
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
    setServiceView(view);
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
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    try {
      if (typeof window !== "undefined" && window.innerWidth < 640) return;
      const raw = sessionStorage.getItem(CHAT_POS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as { x?: unknown; y?: unknown };
      if (typeof parsed.x === "number" && typeof parsed.y === "number") {
        setChatPos({ x: parsed.x, y: parsed.y });
      }
    } catch {
      /* ignore */
    }
  }, []);

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

  const clampChatPos = useCallback((x: number, y: number) => {
    if (typeof window === "undefined") return { x, y };
    const margin = 8;
    const w = Math.min(720, window.innerWidth - margin * 2);
    const h = Math.min(720, window.innerHeight * 0.78, window.innerHeight - 88);
    return {
      x: Math.max(margin, Math.min(x, window.innerWidth - w - margin)),
      y: Math.max(margin, Math.min(y, window.innerHeight - h - margin)),
    };
  }, []);

  const openChat = useCallback(() => {
    // Mobile: always full-sheet — ignore stale drag coordinates that push the panel off-screen.
    try {
      if (typeof window !== "undefined" && window.innerWidth < 640) {
        setChatPos(null);
        sessionStorage.removeItem(CHAT_POS_KEY);
      }
    } catch {
      /* ignore */
    }
    setChatOpen(true);
  }, [CHAT_POS_KEY]);

  const onChatDragStart = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.button !== 0) return;
      const panel = document.getElementById("vector-chat-panel");
      if (!panel) return;
      const rect = panel.getBoundingClientRect();
      const origin = chatPos ?? { x: rect.left, y: rect.top };
      if (!chatPos) setChatPos(origin);
      chatDragRef.current = {
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        originX: origin.x,
        originY: origin.y,
      };
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [chatPos],
  );

  const onChatDragMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      const drag = chatDragRef.current;
      if (!drag || drag.pointerId !== e.pointerId) return;
      setChatPos(
        clampChatPos(
          drag.originX + (e.clientX - drag.startX),
          drag.originY + (e.clientY - drag.startY),
        ),
      );
    },
    [clampChatPos],
  );

  const onChatDragEnd = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      const drag = chatDragRef.current;
      if (!drag || drag.pointerId !== e.pointerId) return;
      chatDragRef.current = null;
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
      setChatPos((prev) => {
        if (!prev) return prev;
        const next = clampChatPos(prev.x, prev.y);
        try {
          sessionStorage.setItem(CHAT_POS_KEY, JSON.stringify(next));
        } catch {
          /* ignore */
        }
        return next;
      });
    },
    [clampChatPos],
  );

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
    const lang = uiLangForMarket(code) as UiLocale;
    if (uiLocale !== lang) {
      applyUiLocale(lang);
    }
  }

  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      const m = (p.get("market") || p.get("country") || "DE").toUpperCase();
      syncLock.current = "market";
      setMarket(m);
      const lang = uiLangForMarket(m) as UiLocale;
      if (uiLocale !== lang) {
        applyUiLocale(lang);
      }
      const view = (p.get("view") || "").toLowerCase();
      if (view === "vector" || window.location.hash.includes("vector")) {
        try {
          if (window.innerWidth < 640) {
            setChatPos(null);
            sessionStorage.removeItem(CHAT_POS_KEY);
          }
        } catch {
          /* ignore */
        }
        setChatOpen(true);
      }
    } catch {
      setMarket("DE");
    }
    // Initial URL → market/lang only once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // LanguageSwitcher is source of truth when buyer picks a UI language.
  useEffect(() => {
    if (syncLock.current === "market") {
      syncLock.current = null;
      return;
    }
    const expectedLang = uiLangForMarket(market);
    if (uiLocale === expectedLang) return;
    const next = canonicalMarketForLang(uiLocale);
    if (next === market) return;
    syncLock.current = "lang";
    setMarket(next);
    writeMarketToUrl(next);
  }, [uiLocale, market]);

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

    fetch(`${api}/api/public/bots/pricing${qs}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        const list = body?.packages;
        if (Array.isArray(list) && list.length > 0) {
          setBotPackages(
            list.map((p: BotPackageCard) => ({
              package_id: String(p.package_id || ""),
              name: String(p.name || ""),
              setup_label: String(p.setup_label || ""),
              monthly_label: String(p.monthly_label || ""),
              price_label: String(p.price_label || ""),
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

  const comingSoon = t("s0.comingSoon", { defaultValue: "Coming Soon" });
  const orderLabel = t("pathA.cta");
  const detailsLabel = t("s0.details", { defaultValue: "Details" });
  const backLabel = t("s0.backToServices", { defaultValue: "← All services" });
  const botOrderHref = (packageId: string) =>
    `/order?market=${encodeURIComponent(market)}&purchase_type=subscription&intent=bot&package=${encodeURIComponent(packageId)}`;

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
                (m.basic_price_label ? ` · ab ${m.basic_price_label}` : "")}
            </option>
          ))}
        </select>
      </div>
    ) : null;

  return (
    <PublicPageShell>
      <div className="relative mx-auto max-w-4xl space-y-12 py-6 pb-28 animate-fade-up">
        {serviceView === "hub" ? (
          <>
            <header className="space-y-4 text-center">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-300/90">
                {BRAND_NAME}
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                {t("s0.hubTitle", {
                  defaultValue: "What do you want to do?",
                })}
              </h1>
              <p className="mx-auto max-w-2xl text-base text-genesis-muted sm:text-lg">
                {t("s0.hubSubtitle", {
                  defaultValue:
                    "Choose a service and order directly — no account required. Register only if you want a personal office for your business.",
                  brand: BRAND_NAME,
                })}
              </p>
              {marketSelect}
              <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
                <a
                  href="#services"
                  className="inline-flex rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  {t("s0.chooseService", {
                    defaultValue: "Choose a service",
                  })}
                </a>
                <Link
                  href="/client/register"
                  className="inline-flex rounded-xl border border-white/20 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/5"
                >
                  {t("s0.createAccount", {
                    defaultValue: "Create personal account",
                  })}
                </Link>
                <Link
                  href="/client/login"
                  className="inline-flex text-sm font-medium text-zinc-400 hover:text-white"
                >
                  {t("s0.signIn", { defaultValue: "Sign in" })}
                </Link>
              </div>
            </header>

            <section
              id="services"
              className="grid gap-4 sm:grid-cols-2"
              aria-label={t("s0.servicesLabel", { defaultValue: "Services" })}
            >
              <button
                type="button"
                onClick={() => openService("websites")}
                className="rounded-2xl border border-emerald-500/35 bg-emerald-950/25 p-6 text-left transition hover:border-emerald-400/50 hover:bg-emerald-950/40"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300/90">
                  {t("s0.cardWebsiteEyebrow", { defaultValue: "Ready today" })}
                </p>
                <h2 className="mt-2 text-xl font-semibold text-white">
                  {t("s0.cardWebsiteTitle", {
                    defaultValue: "Create a website",
                  })}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">
                  {t("s0.cardWebsiteBody", {
                    defaultValue:
                      "Landing packages with clear prices — Basic, Business, Premium.",
                  })}
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-emerald-300">
                  {t("s0.seePackages", { defaultValue: "See packages" })} →
                </span>
              </button>

              <button
                type="button"
                onClick={() => openService("bots")}
                className="rounded-2xl border border-sky-400/30 bg-sky-500/[0.07] p-6 text-left transition hover:border-sky-300/45 hover:bg-sky-500/10"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-200/90">
                  {t("s0.cardBotEyebrow", { defaultValue: "Separate product" })}
                </p>
                <h2 className="mt-2 text-xl font-semibold text-white">
                  {t("s0.cardBotTitle", {
                    defaultValue: "Buy an AI bot",
                  })}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">
                  {t("s0.cardBotBody", {
                    defaultValue:
                      "Business chatbots for your site and Telegram — setup + monthly plan.",
                  })}
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-sky-200">
                  {t("s0.seePackages", { defaultValue: "See packages" })} →
                </span>
              </button>

              <button
                type="button"
                onClick={() => openService("analysis")}
                className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-left transition hover:border-white/25 hover:bg-white/[0.05]"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
                  {t("s0.cardAnalysisEyebrow", { defaultValue: "Free start" })}
                </p>
                <h2 className="mt-2 text-xl font-semibold text-white">
                  {t("s0.cardAnalysisTitle", {
                    defaultValue: "Analyze my website",
                  })}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">
                  {t("s0.cardAnalysisBody", {
                    defaultValue:
                      "See what to fix — then repair or order a new site.",
                  })}
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-zinc-200">
                  {t("s0.startAnalysis", { defaultValue: "Start analysis" })} →
                </span>
              </button>

              <button
                type="button"
                onClick={openChat}
                className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-left transition hover:border-white/25 hover:bg-white/[0.05]"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
                  {ASSISTANT_NAME}
                </p>
                <h2 className="mt-2 text-xl font-semibold text-white">
                  {t("pathA.cardVectorTitle")}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">
                  {t("s0.vectorAsk", {
                    defaultValue: "Not sure what fits? Ask Vector.",
                  })}
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-zinc-200">
                  {t("pathA.meetVectorCta")} →
                </span>
              </button>
            </section>

            <p className="text-center text-xs text-zinc-500">
              {t("s0.hubAccountHint", {
                defaultValue:
                  "No account needed to buy. Register only for your personal office — run projects, bots, automation, upgrades.",
              })}
            </p>
          </>
        ) : null}

        {serviceView === "websites" ? (
          <section id="websites" className="space-y-5" aria-labelledby="websites-heading">
            <button
              type="button"
              onClick={() => openService("hub")}
              className="text-sm font-medium text-emerald-300 hover:underline"
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
            <p className="text-sm text-zinc-400">
              {t("s0.needAccount", {
                defaultValue: "Want an office to manage this later?",
              })}{" "}
              <Link href="/client/register" className="text-emerald-300 hover:underline">
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
              className="text-sm font-medium text-emerald-300 hover:underline"
            >
              {backLabel}
            </button>
            <div>
              <h2 id="bots-heading" className="text-2xl font-semibold text-white">
                {t("s0.botsTitle", { defaultValue: "AI bots" })}
              </h2>
              <p className="mt-1 text-sm text-genesis-muted">
                {t("s0.botsIntro", {
                  defaultValue:
                    "Separate from websites. Order a package directly — no registration required. Open an office later if you want to manage bots and automation.",
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
                botPackages.map((pkg) => (
                  <article
                    key={pkg.package_id}
                    className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
                  >
                    <p className="text-lg font-semibold text-white">{pkg.name}</p>
                    <p className="mt-3 text-2xl font-semibold tracking-tight text-emerald-300">
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
                    <p className="mt-4 flex-1 text-xs leading-relaxed text-zinc-500">
                      Website chat · Telegram · WhatsApp / Instagram in rollout
                    </p>
                    <Link
                      href={botOrderHref(pkg.package_id)}
                      className="mt-5 inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                    >
                      {t("s0.botsCta", {
                        defaultValue: "Order without account",
                      })}
                    </Link>
                  </article>
                ))
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
              className="text-sm font-medium text-emerald-300 hover:underline"
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
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-300/90">
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

        {serviceView === "hub" ? (
        <section
          id="reviews"
          className="rounded-2xl border border-amber-500/25 bg-gradient-to-br from-amber-950/25 via-black/20 to-genesis-panel p-6 sm:p-8"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-lg font-semibold text-white sm:text-xl">
              {t("reviews.title")}
            </h2>
            {reviews?.has_reviews && reviews.average_stars != null ? (
              <p className="text-xs text-amber-200/90">
                ★ {reviews.average_stars} · {reviews.count}{" "}
                {t("reviews.verifiedHint", {
                  defaultValue: "client reviews",
                })}
              </p>
            ) : null}
          </div>
          {!reviews?.has_reviews ? (
            <p className="mt-3 text-sm text-genesis-muted">
              {reviews?.empty_message || t("reviews.empty")}
            </p>
          ) : (
            <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {reviews.reviews.slice(0, 6).map((r) => (
                <li
                  key={r.review_id || r.text.slice(0, 24)}
                  className="rounded-xl border border-white/10 bg-white/[0.04] p-4 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-amber-300">
                      {"★".repeat(Math.max(1, Math.min(5, r.stars)))}
                    </p>
                    {r.verified_purchase ? (
                      <span className="rounded-full border border-emerald-500/30 bg-emerald-950/40 px-2 py-0.5 text-[10px] text-emerald-200">
                        {t("reviews.verifiedPurchase", {
                          defaultValue: "Оплаченный заказ",
                        })}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-white/85">«{r.text}»</p>
                  <p className="mt-2 text-[11px] text-genesis-muted">
                    {[r.company_display_name, r.service_label].filter(Boolean).join(" · ") ||
                      t("reviews.client", { defaultValue: "Клиент" })}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
        ) : null}

        {serviceView === "hub" ? (
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
        ) : null}

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
            <Link href="/client/register" className="font-medium text-emerald-300 hover:underline">
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

        <p className="text-center text-xs text-white/40">
          {t("pathA.foot", { brand: BRAND_NAME })}
        </p>

        {/* Vector chat — mobile full sheet; desktop floating card */}
        {chatOpen ? (
          <div
            id="vector-chat-panel"
            style={
              chatPos
                ? {
                    left: chatPos.x,
                    top: chatPos.y,
                    right: "auto",
                    bottom: "auto",
                    maxHeight: vvLayout.height
                      ? `${Math.max(280, vvLayout.height - 16)}px`
                      : undefined,
                  }
                : undefined
            }
            className={`fixed inset-0 z-[60] flex h-dvh max-h-dvh w-full flex-col overflow-hidden border-0 border-sky-400/30 bg-genesis-bg shadow-2xl sm:inset-auto sm:bottom-6 sm:right-6 sm:left-auto sm:h-[min(78dvh,720px)] sm:max-h-[min(78dvh,720px)] sm:w-[min(720px,calc(100vw-3rem))] sm:rounded-2xl sm:border ${
              chatPos
                ? "max-sm:!inset-0 max-sm:!left-0 max-sm:!top-0 max-sm:!right-0 max-sm:!bottom-0 max-sm:!max-h-none"
                : ""
            }`}
          >
            <div
              className="flex shrink-0 touch-none items-center justify-between gap-2 border-b border-white/10 px-3 py-2.5 sm:cursor-grab sm:active:cursor-grabbing sm:px-4"
              onPointerDown={(e) => {
                if (typeof window !== "undefined" && window.innerWidth < 640) return;
                onChatDragStart(e);
              }}
              onPointerMove={onChatDragMove}
              onPointerUp={onChatDragEnd}
              onPointerCancel={onChatDragEnd}
              title={t("s0.dragChat", {
                defaultValue: "Drag to move",
              })}
            >
              <div className="flex min-w-0 items-center gap-2">
                <span
                  className="hidden select-none text-zinc-500 sm:inline"
                  aria-hidden
                >
                  ⠿
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">
                    {ASSISTANT_NAME}
                  </p>
                  <p className="truncate text-xs text-zinc-400">
                    {t("s0.chatHint", {
                      defaultValue: "Consultant — ask anything about packages",
                    })}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen(false)}
                onPointerDown={(e) => e.stopPropagation()}
                className="rounded-lg px-3 py-2 text-sm text-zinc-400 hover:bg-white/5 hover:text-white"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden [&_#genesis-chat]:h-full [&_#genesis-chat]:max-h-none [&_#genesis-chat]:min-h-0 [&_#genesis-chat]:rounded-none [&_#genesis-chat]:border-0 [&_#genesis-chat]:shadow-none">
              <GenesisConcierge scope="public" />
            </div>
          </div>
        ) : null}

        {!chatOpen ? (
          <button
            type="button"
            onClick={() => openChat()}
            className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-sky-400/40 bg-sky-600 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:brightness-110"
            style={
              vvLayout.keyboard > 0
                ? { bottom: `max(1.25rem, ${vvLayout.keyboard + 12}px)` }
                : undefined
            }
          >
            {t("s0.askVector", { defaultValue: "Ask Vector" })}
          </button>
        ) : null}
      </div>
    </PublicPageShell>
  );
}
