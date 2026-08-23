"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BRAND_NAME } from "../../lib/publicBrand";
import { formatLocalizedMoney } from "../../lib/formatEur";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import { LANDING_PACKAGES_EUR } from "../../lib/commercialCatalog";
import { CHATBOT_PRICE_TIERS } from "./modules";
import { PUBLIC_VITRINE_THUMB_VERSION, PUBLIC_AGENCY_PORTFOLIO } from "../../lib/publicVitrineCatalog";
import {
  agencyCardSurface,
  agencyTierPill,
} from "../../lib/agencySelectionStyles";

type PublicReviews = {
  has_reviews: boolean;
  count: number;
  average_stars: number | null;
  empty_message?: string | null;
  reviews: {
    review_id?: string;
    stars: number;
    text: string;
    company_display_name?: string | null;
    service_label?: string | null;
    verified_purchase?: boolean;
  }[];
};

type HubBotPackage = {
  package_id: string;
  name: string;
  setup_label: string;
  monthly_label: string;
  price_label: string;
};

type Props = {
  market: string;
  localeTag: string;
  marketSelect: ReactNode;
  reviews: PublicReviews | null;
  botPackages?: HubBotPackage[];
  onOpenWebsites: () => void;
  onOpenBots: () => void;
  onOpenAnalysis: () => void;
  orderHrefFor: (packageId: string) => string;
  botOrderHrefFor?: (packageId: string) => string;
};

type PortfolioLive = {
  id: string;
  title: string;
  tag: string;
  href: string;
  thumb: string;
};

const THUMB_V = PUBLIC_VITRINE_THUMB_VERSION;

/** Honest agency showcase — one artifact id for card + Besuchen (publicVitrineCatalog SSOT). */
const PORTFOLIO: PortfolioLive[] = PUBLIC_AGENCY_PORTFOLIO.filter(
  (item) => item.showcaseStatus === "PUBLISHED",
).map((item) => ({
  id: item.id,
  title: item.title,
  tag: item.tag,
  href: item.livePreviewUrl,
  thumb: `${item.previewImage}?v=${THUMB_V}`,
}));

const WEBSITE_TIERS = ["basic", "business", "premium"] as const;
type WebsiteTierId = (typeof WEBSITE_TIERS)[number];

function IconGlobe({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M3 12h18M12 3c2.5 2.8 3.8 5.8 3.8 9S14.5 18.2 12 21c-2.5-2.8-3.8-5.8-3.8-9S9.5 5.8 12 3Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function IconCart({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 5h2l1.6 9.2a2 2 0 0 0 2 1.6h7.6a2 2 0 0 0 2-1.5L21 8H7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="10" cy="20" r="1.2" fill="currentColor" />
      <circle cx="18" cy="20" r="1.2" fill="currentColor" />
    </svg>
  );
}

function IconAi({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function IconExternal({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M14 5h5v5M19 5l-9 9M10 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BrowserFrame({
  src,
  alt,
  className = "",
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    <div
      className={`overflow-hidden rounded-xl border border-white/12 bg-[#0a0a0f] shadow-[0_24px_80px_-20px_rgba(124,58,237,0.45)] ${className}`}
    >
      <div className="flex items-center gap-1.5 border-b border-white/8 bg-white/[0.03] px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-white/20" />
        <span className="h-2 w-2 rounded-full bg-white/20" />
        <span className="h-2 w-2 rounded-full bg-white/20" />
        <span className="ml-2 h-1.5 flex-1 rounded-full bg-white/8" />
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        className="aspect-[16/10] w-full object-cover"
        loading="lazy"
      />
    </div>
  );
}

export function CommercialAgencyHub({
  market,
  localeTag,
  marketSelect,
  reviews,
  botPackages,
  onOpenWebsites,
  onOpenBots,
  onOpenAnalysis,
  orderHrefFor,
  botOrderHrefFor,
}: Props) {
  const { t } = useTranslation("site");
  const ns = "agencyHub";
  const [websiteTier, setWebsiteTier] = useState<WebsiteTierId>("business");
  const [activeProduct, setActiveProduct] = useState<"website" | "shop" | "ai">("website");

  const tierLabel = (id: WebsiteTierId) => {
    if (id === "basic") return "Basic";
    if (id === "business") return "Business";
    return "Premium";
  };

  const tierPrice = (id: WebsiteTierId) =>
    formatLocalizedMoney(LANDING_PACKAGES_EUR[id], "EUR", localeTag);

  const websiteFrom = formatLocalizedMoney(
    LANDING_PACKAGES_EUR.basic,
    "EUR",
    localeTag,
  );
  const shopPrice = formatLocalizedMoney(799, "EUR", localeTag);
  const botAnchor =
    botPackages?.find((p) => p.package_id === "bot_starter") ||
    botPackages?.[0];
  const botSetup =
    botAnchor?.setup_label ||
    formatLocalizedMoney(CHATBOT_PRICE_TIERS[0].setupEur, "EUR", localeTag);
  const botMonthly =
    botAnchor?.monthly_label ||
    formatLocalizedMoney(CHATBOT_PRICE_TIERS[0].monthlyEur, "EUR", localeTag);

  const shopHref = `/order/shop?market=${encodeURIComponent(market)}`;
  const botHref =
    botOrderHrefFor?.("bot_starter") ||
    `/order/bot?market=${encodeURIComponent(market)}&package=bot_starter`;
  const websiteOrderHref = orderHrefFor(websiteTier);

  const products = [
    {
      id: "website" as const,
      icon: IconGlobe,
      title: t(`${ns}.products.website`, { defaultValue: "Website" }),
      price: t(`${ns}.products.fromPrice`, {
        defaultValue: "ab {{price}}",
        price: websiteFrom,
      }),
      billing: t(`${ns}.products.oneTime`, { defaultValue: "Einmalig" }),
      points: [
        t(`${ns}.products.web1`, { defaultValue: "Branche & Marke — fertige Website" }),
        t(`${ns}.products.web2`, { defaultValue: "Responsive · Kontakt · Legal" }),
        t(`${ns}.products.web3`, {
          defaultValue: "Pakete Basic / Business / Premium",
        }),
      ],
      href: websiteOrderHref,
      secondary: onOpenWebsites,
      secondaryLabel: t(`${ns}.products.compare`, { defaultValue: "Pakete vergleichen" }),
      featured: false,
      orderEvent: websiteTier,
    },
    {
      id: "shop" as const,
      icon: IconCart,
      title: t(`${ns}.products.shop`, { defaultValue: "Online-Shop" }),
      price: t(`${ns}.products.fromPrice`, {
        defaultValue: "ab {{price}}",
        price: shopPrice,
      }),
      billing: t(`${ns}.products.oneTime`, { defaultValue: "Einmalig" }),
      points: [
        t(`${ns}.products.shop1`, { defaultValue: "Katalog · Warenkorb · Shop Admin" }),
        t(`${ns}.products.shop2`, {
          defaultValue: "Stripe / Versand / E-Mail — Ihre Konten",
        }),
        t(`${ns}.products.shop3`, { defaultValue: "AI Store Basic / Start" }),
      ],
      href: shopHref,
      secondary: null as (() => void) | null,
      secondaryLabel: "",
      featured: true,
      orderEvent: "shop",
    },
    {
      id: "ai" as const,
      icon: IconAi,
      title: t(`${ns}.products.ai`, { defaultValue: "AI Business Assistant" }),
      price: t(`${ns}.products.fromPrice`, {
        defaultValue: "ab {{price}}",
        price: botSetup,
      }),
      billing: t(`${ns}.products.thenMonthly`, {
        defaultValue: "+ {{monthly}}/Monat",
        monthly: botMonthly,
      }),
      points: [
        t(`${ns}.products.ai1`, { defaultValue: "Telegram + Website Chat live" }),
        t(`${ns}.products.ai2`, { defaultValue: "Leads · Buchungen · 24/7 Antworten" }),
        t(`${ns}.products.ai3`, {
          defaultValue: "WhatsApp / IG / Messenger — Coming soon",
        }),
      ],
      href: botHref,
      secondary: onOpenBots,
      secondaryLabel: t(`${ns}.products.aiTiers`, { defaultValue: "Stufen ansehen" }),
      featured: false,
      orderEvent: "bot_starter",
    },
  ] as const;

  const moreServices: {
    id: string;
    label: string;
    live: boolean;
    onClick?: () => void;
    href?: string;
  }[] = [
    {
      id: "analysis",
      label: t(`${ns}.more.analysis`, { defaultValue: "Website Analysis" }),
      live: true,
      onClick: onOpenAnalysis,
    },
    {
      id: "repair",
      label: t(`${ns}.more.repair`, { defaultValue: "Website Repair" }),
      live: true,
      href: `/order/service/website_repair?market=${encodeURIComponent(market)}&form=1`,
    },
    {
      id: "automation",
      label: t(`${ns}.more.automation`, { defaultValue: "Automation" }),
      live: false,
    },
    {
      id: "crm",
      label: t(`${ns}.more.crm`, { defaultValue: "CRM" }),
      live: false,
    },
    {
      id: "seo",
      label: t(`${ns}.more.seo`, { defaultValue: "SEO" }),
      live: false,
    },
    {
      id: "marketing",
      label: t(`${ns}.more.marketing`, { defaultValue: "Marketing" }),
      live: false,
    },
  ];

  const heroThumb = PORTFOLIO[0]?.thumb;

  return (
    <div className="agency-hub relative space-y-16 sm:space-y-24">
      {/* HERO */}
      <section className="agency-hub__hero relative grid items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-12">
        <div className="relative z-10 space-y-6 text-left">
          <p className="inline-flex items-center rounded-full border border-violet-400/35 bg-violet-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-violet-200">
            {t(`${ns}.hero.badge`, { defaultValue: "Digital Solutions" })}
          </p>
          <div>
            <p className="text-sm font-semibold tracking-[0.28em] text-white/70">
              {BRAND_NAME.toUpperCase()}
            </p>
            <h1 className="mt-3 max-w-[18ch] text-[2.15rem] font-semibold leading-[1.08] tracking-[-0.03em] text-white sm:text-5xl lg:text-[3.25rem]">
              {t(`${ns}.hero.title`, {
                defaultValue: "Digitale Lösungen für Ihr Business",
              })}
            </h1>
          </div>
          <p className="max-w-md text-base leading-relaxed text-zinc-300 sm:text-lg">
            {t(`${ns}.hero.sub`, {
              defaultValue: "Websites, Online-Shops & AI Business Assistant.",
            })}
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="#produkte"
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-violet-600 px-7 py-3.5 text-sm font-semibold text-white shadow-[0_12px_40px_-12px_rgba(124,58,237,0.9)] transition hover:bg-violet-500"
            >
              {t(`${ns}.hero.cta`, { defaultValue: "Projekt starten" })}
            </Link>
            <a
              href="#projekte"
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/20 px-7 py-3.5 text-sm font-semibold text-white transition hover:border-violet-400/50 hover:bg-white/[0.04]"
            >
              {t(`${ns}.hero.projects`, { defaultValue: "Projekte ansehen" })}
            </a>
          </div>
          <div className="max-w-sm pt-1">{marketSelect}</div>
          <p className="text-[11px] leading-relaxed text-zinc-500">
            {t(`${ns}.hero.ki`, {
              defaultValue:
                "Inhalte werden KI-gestützt erstellt. Nach dem Kauf können Sie Änderungen anfordern.",
            })}{" "}
            <Link href="/ai-disclaimer" className="text-violet-300 hover:underline">
              {t(`${ns}.hero.kiLink`, { defaultValue: "KI-Hinweis" })}
            </Link>
          </p>
        </div>

        <div className="agency-hub__hero-visual relative mx-auto w-full max-w-lg lg:max-w-none">
          <div
            className="pointer-events-none absolute -inset-8 rounded-[2rem] bg-[radial-gradient(ellipse_at_center,rgba(124,58,237,0.28),transparent_65%)]"
            aria-hidden
          />
          <div className="relative">
            {heroThumb ? (
              <BrowserFrame
                src={heroThumb}
                alt={t(`${ns}.hero.mockAlt`, {
                  defaultValue: "Beispiel einer generierten Website",
                })}
                className="agency-hub__float relative z-10"
              />
            ) : null}
            <div className="agency-hub__orb absolute -left-3 top-8 z-20 sm:-left-6" aria-hidden>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/40 bg-[#12101a] text-violet-200 shadow-lg sm:h-14 sm:w-14">
                <IconGlobe className="h-6 w-6" />
              </div>
            </div>
            <div
              className="agency-hub__orb agency-hub__orb--delay absolute -right-2 top-1/3 z-20 sm:-right-5"
              aria-hidden
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/40 bg-[#12101a] text-violet-200 shadow-lg sm:h-14 sm:w-14">
                <IconCart className="h-6 w-6" />
              </div>
            </div>
            <div
              className="agency-hub__orb agency-hub__orb--delay2 absolute bottom-6 left-1/2 z-20 -translate-x-1/2 sm:bottom-8"
              aria-hidden
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/40 bg-[#12101a] text-violet-200 shadow-lg sm:h-14 sm:w-14">
                <IconAi className="h-6 w-6" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PRODUKTE */}
      <section id="produkte" className="scroll-mt-24 space-y-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.products.title`, { defaultValue: "Unsere Produkte" })}
          </h2>
          <p className="mt-3 text-sm text-zinc-400 sm:text-base">
            {t(`${ns}.products.sub`, {
              defaultValue: "Drei fertige Wege — klare Preise, echte Bestellung.",
            })}
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {products.map((p) => {
            const Icon = p.icon;
            const isWebsite = p.id === "website";
            const isSelected = activeProduct === p.id;
            const cardSelected = isSelected || (isWebsite && activeProduct === "website");
            return (
              <article
                key={p.id}
                className={`flex flex-col rounded-2xl border p-5 sm:p-6 ${agencyCardSurface(
                  cardSelected,
                  p.featured && !cardSelected,
                )}`}
                onClick={() => setActiveProduct(p.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") setActiveProduct(p.id);
                }}
                role="button"
                tabIndex={0}
              >
                {p.featured && !cardSelected ? (
                  <span className="mb-3 inline-flex w-fit rounded-full border border-violet-400/40 bg-violet-500/15 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-violet-100">
                    {t(`${ns}.products.bestseller`, { defaultValue: "Bestseller" })}
                  </span>
                ) : cardSelected ? (
                  <span className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full border border-violet-400/50 bg-violet-500/20 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-violet-100">
                    <span aria-hidden>✓</span>
                    {t(`${ns}.products.selected`, { defaultValue: "Ausgewählt" })}
                  </span>
                ) : (
                  <span className="mb-3 block h-5" aria-hidden />
                )}
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-violet-400/25 bg-violet-500/10 text-violet-200">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-xl font-semibold text-white">{p.title}</h3>
                {isWebsite ? (
                  <>
                    <p className="mt-2 text-sm text-zinc-400">
                      {t(`${ns}.products.pickTier`, {
                        defaultValue: "Paket wählen",
                      })}
                    </p>
                    <div className="mt-3 grid grid-cols-3 gap-1.5">
                      {WEBSITE_TIERS.map((tier) => {
                        const tierSelected = websiteTier === tier;
                        return (
                          <button
                            key={tier}
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveProduct("website");
                              setWebsiteTier(tier);
                            }}
                            className={`rounded-xl border px-2 py-2 text-center text-[11px] font-semibold transition ${agencyTierPill(tierSelected)}`}
                          >
                            <span className="block">{tierLabel(tier)}</span>
                            <span className="mt-0.5 block text-[10px] font-normal opacity-90">
                              {tierPrice(tier)}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                    <p className="mt-3 text-lg font-semibold text-white">
                      {t(`${ns}.products.selectedLine`, {
                        defaultValue: "✓ Website — {{tier}} ausgewählt",
                        tier: tierLabel(websiteTier),
                      })}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="mt-2 text-3xl font-semibold tracking-tight text-white">
                      {p.price}
                    </p>
                    <p className="mt-1 text-sm text-zinc-400">{p.billing}</p>
                  </>
                )}
                <ul className="mt-5 flex-1 space-y-2 text-sm text-zinc-300">
                  {p.points.map((line) => (
                    <li key={line} className="flex gap-2">
                      <span className="mt-0.5 text-violet-400" aria-hidden>
                        ✓
                      </span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={p.href}
                  onClick={(e) => {
                    e.stopPropagation();
                    logCommerceEvent("tier_select", p.orderEvent, "site");
                  }}
                  className={`mt-6 inline-flex min-h-[44px] items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition ${
                    cardSelected
                      ? "bg-violet-600 shadow-[0_12px_40px_-12px_rgba(124,58,237,0.9)] hover:bg-violet-500"
                      : "bg-violet-600/90 hover:bg-violet-500"
                  }`}
                >
                  {t(`${ns}.products.cta`, { defaultValue: "Jetzt bestellen" })}
                </Link>
                {p.secondary ? (
                  <button
                    type="button"
                    onClick={p.secondary}
                    className="mt-2 text-center text-xs font-medium text-violet-300/90 hover:underline"
                  >
                    {p.secondaryLabel}
                  </button>
                ) : null}
              </article>
            );
          })}
        </div>
      </section>

      {/* WEITERE SERVICES */}
      <section id="services" className="scroll-mt-24 space-y-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.more.title`, { defaultValue: "Weitere Services" })}
          </h2>
          <p className="mt-2 text-sm text-zinc-400">
            {t(`${ns}.more.sub`, {
              defaultValue: "Live bestellbar oder Coming soon — ohne leere Versprechen.",
            })}
          </p>
        </div>
        <ul className="mx-auto grid max-w-4xl gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {moreServices.map((s) => {
            const inner = (
              <>
                <span className="font-medium text-white">{s.label}</span>
                <span
                  className={`text-[10px] font-semibold uppercase tracking-wider ${
                    s.live ? "text-violet-300" : "text-zinc-500"
                  }`}
                >
                  {s.live
                    ? t(`${ns}.more.live`, { defaultValue: "Live" })
                    : t(`${ns}.more.soon`, { defaultValue: "Coming soon" })}
                </span>
              </>
            );
            const cls =
              "flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3.5 text-left transition hover:border-violet-500/35";
            if (s.live && s.onClick) {
              return (
                <li key={s.id}>
                  <button type="button" onClick={s.onClick} className={`${cls} w-full`}>
                    {inner}
                  </button>
                </li>
              );
            }
            if (s.live && s.href) {
              return (
                <li key={s.id}>
                  <Link href={s.href} className={cls}>
                    {inner}
                  </Link>
                </li>
              );
            }
            return (
              <li key={s.id}>
                <div className={`${cls} cursor-default opacity-70`}>{inner}</div>
              </li>
            );
          })}
        </ul>
      </section>

      {/* UNSERE PROJEKTE */}
      <section id="projekte" className="scroll-mt-24 space-y-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.projects.title`, { defaultValue: "Unsere Projekte" })}
          </h2>
          <p className="mt-3 text-sm text-zinc-400 sm:text-base">
            {t(`${ns}.projects.sub`, {
              defaultValue:
                "Echte Factory-Builds. Weitere Branchen erscheinen hier, sobald sie freigegeben sind.",
            })}
          </p>
        </div>
        <ul className="mx-auto grid max-w-5xl gap-6 sm:grid-cols-2">
          {PORTFOLIO.map((item) => (
            <li key={item.id}>
              <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0c0a12] shadow-[0_24px_80px_-32px_rgba(124,58,237,0.35)]">
                <a
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block overflow-hidden"
                >
                  <BrowserFrame
                    src={item.thumb}
                    alt={item.title}
                    className="rounded-none border-0 shadow-none transition duration-500 group-hover:brightness-110"
                  />
                </a>
                <div className="flex flex-1 items-end justify-between gap-3 p-5">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                    <p className="mt-0.5 text-sm text-violet-300/90">{item.tag}</p>
                  </div>
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-violet-400/40 px-3 py-2 text-xs font-semibold text-violet-100 transition hover:bg-violet-500/15"
                  >
                    {t(`${ns}.projects.visit`, { defaultValue: "Besuchen" })}
                    <IconExternal className="h-3.5 w-3.5" />
                  </a>
                </div>
              </article>
            </li>
          ))}
        </ul>
      </section>

      {/* WARUM */}
      <section id="warum" className="scroll-mt-24 mx-auto max-w-3xl space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.why.title`, { defaultValue: "Warum Virtus Core" })}
          </h2>
          <p className="mt-2 text-sm text-zinc-400">
            {t(`${ns}.why.sub`, {
              defaultValue:
                "Digitale Firma statt Agentur-Warteschlange — Sie bestellen, erhalten und steuern.",
            })}
          </p>
        </div>
        <ul className="grid gap-3 sm:grid-cols-3">
          {(
            [
              {
                t: `${ns}.why.p1t`,
                d: `${ns}.why.p1d`,
                tf: "Klare Preise",
                df: "Website, Shop und AI — ohne versteckte Agentur-Stunden.",
              },
              {
                t: `${ns}.why.p2t`,
                d: `${ns}.why.p2d`,
                tf: "Schnelle Lieferung",
                df: "Factory baut nach der Zahlung. Sie prüfen und veröffentlichen.",
              },
              {
                t: `${ns}.why.p3t`,
                d: `${ns}.why.p3d`,
                tf: "Ihr Panel",
                df: "Ab Business: Client Workspace — Inhalte und Medien selbst ändern.",
              },
            ] as const
          ).map((row) => (
            <li
              key={row.t}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-left"
            >
              <p className="font-semibold text-white">
                {t(row.t, { defaultValue: row.tf })}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                {t(row.d, { defaultValue: row.df })}
              </p>
            </li>
          ))}
        </ul>
        <p className="text-center text-sm">
          <Link href="/why" className="font-medium text-violet-300 hover:underline">
            {t(`${ns}.why.link`, { defaultValue: "Vergleich mit Agenturen →" })}
          </Link>
        </p>
      </section>

      {/* Reviews — only if real */}
      {reviews?.has_reviews ? (
        <section
          id="reviews"
          className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 sm:p-8"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="text-xl font-semibold text-white">
              {t("reviews.title")}
            </h2>
            <Link
              href="/trust"
              className="text-xs font-semibold text-violet-300 hover:underline"
            >
              {t(`${ns}.reviews.leave`, { defaultValue: "Bewertung hinterlassen" })}
            </Link>
          </div>
          <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {reviews.reviews.slice(0, 6).map((r) => (
              <li
                key={r.review_id || r.text.slice(0, 24)}
                className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm"
              >
                <p className="text-amber-300">
                  {"★".repeat(Math.max(1, Math.min(5, r.stars)))}
                </p>
                <p className="mt-2 text-zinc-200">«{r.text}»</p>
                <p className="mt-2 text-[11px] text-zinc-500">
                  {[r.company_display_name, r.service_label].filter(Boolean).join(" · ") ||
                    t("reviews.client", { defaultValue: "Client" })}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* FINAL CTA */}
      <section
        id="starten"
        className="relative overflow-hidden rounded-[1.75rem] border border-violet-500/35 bg-gradient-to-br from-violet-950/60 via-[#0c0a14] to-black px-6 py-12 text-center sm:px-10 sm:py-16"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(139,92,246,0.22),transparent_55%)]"
          aria-hidden
        />
        <div className="relative z-10 mx-auto max-w-xl space-y-5">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.final.title`, {
              defaultValue: "Bereit, Ihr Projekt zu starten?",
            })}
          </h2>
          <p className="text-sm text-zinc-300 sm:text-base">
            {t(`${ns}.final.sub`, {
              defaultValue:
                "Wählen Sie Website, Shop oder AI Assistant — Zahlung und Lieferung über den bestehenden Bestellweg.",
            })}
          </p>
          <div className="flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
            <Link
              href={websiteOrderHref}
              onClick={() => logCommerceEvent("tier_select", "business", "site")}
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-violet-600 px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-violet-500"
            >
              {t(`${ns}.final.cta`, { defaultValue: "Projekt starten" })}
            </Link>
            <Link
              href="/kontakt"
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/25 px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-white/[0.05]"
            >
              {t(`${ns}.final.consult`, { defaultValue: "Beratung anfragen" })}
            </Link>
          </div>
        </div>
      </section>

      <nav
        className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-center text-[11px] text-zinc-500"
        aria-label="Legal"
      >
        <Link href="/client/register" className="hover:text-zinc-300 hover:underline">
          {t("s0.createAccount", { defaultValue: "Konto erstellen" })}
        </Link>
        <Link href="/client/login" className="hover:text-zinc-300 hover:underline">
          {t("s0.signIn", { defaultValue: "Anmelden" })}
        </Link>
        <Link href="/impressum" className="hover:text-zinc-300 hover:underline">
          Impressum
        </Link>
        <Link href="/datenschutz" className="hover:text-zinc-300 hover:underline">
          Datenschutz
        </Link>
        <Link href="/ai-disclaimer" className="hover:text-zinc-300 hover:underline">
          {t(`${ns}.hero.kiLink`, { defaultValue: "KI-Hinweis" })}
        </Link>
      </nav>
    </div>
  );
}
