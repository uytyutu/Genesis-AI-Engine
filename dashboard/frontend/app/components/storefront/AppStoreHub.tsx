"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { BRAND_NAME, ASSISTANT_NAME } from "../../lib/publicBrand";
import { formatLocalizedMoney } from "../../lib/formatEur";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import { LiveActivityCanvas } from "./LiveActivityCanvas";
import {
  CHATBOT_PRICE_TIERS,
  STORE_MODULES_PRIMARY,
  STORE_MODULES_SOON,
  WEBSITE_PRICE_TIERS,
  type StoreModule,
} from "./modules";
import { ServiceCatalogGrid } from "../ServiceCatalogCards";

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

type HubPackage = {
  id: string;
  name: string;
  price_eur: number;
  currency?: string;
  price_label?: string;
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
  packages?: HubPackage[];
  botPackages?: HubBotPackage[];
  onOpenVector: () => void;
  onOpenWebsites: () => void;
  onOpenBots: () => void;
  onOpenAnalysis: () => void;
  orderHrefFor: (packageId: string) => string;
  botOrderHrefFor?: (packageId: string) => string;
};

function stars(n: number) {
  if (n <= 0) return "☆☆☆☆☆";
  return "★".repeat(Math.min(5, n)) + "☆".repeat(Math.max(0, 5 - n));
}

function moduleAction(
  mod: StoreModule,
  handlers: {
    onOpenVector: () => void;
    onOpenWebsites: () => void;
    onOpenBots: () => void;
    onOpenAnalysis: () => void;
    onOpenStore: () => void;
  },
) {
  switch (mod.action) {
    case "websites":
      return handlers.onOpenWebsites;
    case "store":
      return handlers.onOpenStore;
    case "bots":
    case "orderBot":
      return handlers.onOpenBots;
    case "analysis":
      return handlers.onOpenAnalysis;
    case "vector":
      return handlers.onOpenVector;
    default:
      return null;
  }
}

export function AppStoreHub({
  market,
  localeTag,
  marketSelect,
  reviews,
  packages,
  botPackages,
  onOpenVector,
  onOpenWebsites,
  onOpenBots,
  onOpenAnalysis,
  orderHrefFor,
  botOrderHrefFor,
}: Props) {
  const { t } = useTranslation("site");
  const ns = "appStore";

  const handlers = {
    onOpenVector,
    onOpenWebsites,
    onOpenBots,
    onOpenAnalysis,
    onOpenStore: () => {
      if (typeof window !== "undefined") {
        window.location.href = `/order/shop?market=${encodeURIComponent(market)}`;
      }
    },
  };

  const renderModuleCard = (mod: StoreModule) => {
    const go = moduleAction(mod, handlers);
    const live = mod.status === "live";
    const badgeKey =
      mod.badge === "popular"
        ? "modules.badgePopular"
        : mod.badge === "new"
          ? "modules.badgeNew"
          : mod.badge === "choice"
            ? "modules.badgeChoice"
            : null;
    return (
      <article
        key={mod.id}
        className="storefront-module-card group flex flex-col rounded-3xl border border-white/10 bg-white/[0.03] p-5"
      >
        <div className="flex items-start justify-between gap-2">
          <span className="text-2xl transition group-hover:scale-110" aria-hidden>
            {mod.icon}
          </span>
          <div className="flex flex-wrap justify-end gap-1">
            {badgeKey ? (
              <span className="rounded-full border border-fuchsia-400/35 bg-fuchsia-950/40 px-2 py-0.5 text-[10px] font-semibold text-fuchsia-100">
                {t(`${ns}.${badgeKey}`)}
              </span>
            ) : null}
            {live ? (
              <span className="rounded-full border border-emerald-500/30 bg-emerald-950/40 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-200">
                {t(`${ns}.modules.live`, { defaultValue: "Live" })}
              </span>
            ) : (
              <span className="rounded-full border border-amber-500/30 bg-amber-950/30 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-100/90">
                {t(`${ns}.modules.soon`, { defaultValue: "Coming Soon" })}
              </span>
            )}
          </div>
        </div>
        <h3 className="mt-3 text-lg font-semibold text-white">
          {t(`${ns}.${mod.nameKey}`)}
        </h3>
        {live ? (
          <p className="mt-1 text-xs text-amber-200/80">{stars(mod.rating)}</p>
        ) : null}
        <p className="mt-2 flex-1 text-sm text-genesis-muted">
          {t(`${ns}.${mod.blurbKey}`)}
        </p>
        {mod.availableChannelsKey ? (
          <div className="mt-3 space-y-1 text-xs text-zinc-400">
            <p className="font-semibold text-emerald-200/90">
              {t(`${ns}.${mod.availableChannelsKey}`, {
                defaultValue: "Available today: Telegram",
              })}
            </p>
            {mod.comingSoonChannelsKey ? (
              <p>
                {t(`${ns}.${mod.comingSoonChannelsKey}`, {
                  defaultValue:
                    "Coming soon: Website Chat, WhatsApp, Instagram, Messenger",
                })}
              </p>
            ) : null}
          </div>
        ) : null}
        {live && go ? (
          <button
            type="button"
            onClick={() => {
              logCommerceEvent("module_try", mod.id, "site");
              go();
            }}
            className="storefront-module-cta mt-4 inline-flex items-center justify-center rounded-xl bg-genesis-purple-soft px-4 py-2.5 text-sm font-semibold text-white"
          >
            {t(`${ns}.modules.try`, { defaultValue: "Open" })}
          </button>
        ) : (
          <button
            type="button"
            disabled
            className="mt-4 inline-flex cursor-not-allowed items-center justify-center rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-zinc-500"
          >
            {t(`${ns}.modules.notify`, { defaultValue: "Coming Soon" })}
          </button>
        )}
      </article>
    );
  };

  const websiteTiers =
    packages && packages.length > 0
      ? packages
          .filter((p) => ["basic", "business", "premium"].includes(String(p.id)))
          .map((p) => ({
            id: p.id,
            priceLabel:
              p.price_label ||
              formatLocalizedMoney(p.price_eur, p.currency || "EUR", localeTag),
            name: p.name,
            featured: p.id === "business",
          }))
      : WEBSITE_PRICE_TIERS.map((tier) => ({
          id: tier.id,
          priceLabel: formatLocalizedMoney(tier.priceEur, "EUR", localeTag),
          name: t(`${ns}.${tier.nameKey}`),
          featured: "featured" in tier && Boolean(tier.featured),
          blurbKey: tier.blurbKey,
        }));

  const botTiers =
    botPackages && botPackages.length > 0
      ? botPackages
          .filter((p) => String(p.package_id || "").startsWith("bot_"))
          .map((p) => {
            const fallback = CHATBOT_PRICE_TIERS.find((t) => t.id === p.package_id);
            return {
              id: p.package_id,
              name: p.name,
              setupLabel: p.setup_label || p.price_label,
              monthlyLabel: p.monthly_label || "",
              featured: p.package_id.includes("business"),
              outcomeKeys: fallback?.outcomeKeys ?? ([] as const),
              blurbKey: fallback?.blurbKey,
            };
          })
      : CHATBOT_PRICE_TIERS.map((tier) => ({
          id: tier.id,
          name: t(`${ns}.${tier.nameKey}`),
          setupLabel: formatLocalizedMoney(tier.setupEur, "EUR", localeTag),
          monthlyLabel: formatLocalizedMoney(tier.monthlyEur, "EUR", localeTag),
          featured: "featured" in tier && Boolean(tier.featured),
          blurbKey: tier.blurbKey,
          outcomeKeys: tier.outcomeKeys,
        }));

  const botHref = (id: string) =>
    botOrderHrefFor?.(id) || `/order/bot?package=${encodeURIComponent(id)}`;

  return (
    <div className="storefront relative space-y-16 sm:space-y-20">
      {/* Hero — mobile-first: readable first screen without toast clutter */}
      <section className="relative overflow-hidden rounded-2xl border border-genesis-purple/30 bg-black/15 px-4 py-10 shadow-[0_0_80px_-24px_rgba(124,58,237,0.55)] backdrop-blur-md sm:rounded-[2rem] sm:px-10 sm:py-16">
        <LiveActivityCanvas />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-violet-950/20 via-transparent to-black/40" aria-hidden />
        <div className="relative z-10 mx-auto max-w-3xl space-y-5 text-center sm:space-y-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-genesis-purple">
            {BRAND_NAME}
          </p>
          <h1 className="text-[2rem] font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            <span className="block">{t(`${ns}.hero.line1`, { defaultValue: "Your business." })}</span>
            <span className="mt-1 block bg-gradient-to-r from-genesis-purple via-fuchsia-300 to-genesis-accent bg-clip-text text-transparent">
              {t(`${ns}.hero.line2`, { defaultValue: "Next generation." })}
            </span>
          </h1>
          <p className="mx-auto max-w-xl text-base font-medium text-white/90 sm:text-lg">
            {t(`${ns}.hero.emotion`, {
              defaultValue: "AI is ready to work for your business.",
            })}
          </p>
          <p className="mx-auto max-w-xl text-sm text-genesis-muted sm:text-base">
            {t(`${ns}.hero.sub`, {
              defaultValue: "One AI. Websites. Chatbots. Automation. Analytics.",
              brand: BRAND_NAME,
            })}
          </p>
          <ul className="flex flex-wrap items-center justify-center gap-2 text-xs text-white/70 sm:text-sm">
            {(["pillAi", "pillSites", "pillBots", "pillAuto", "pillAnalytics"] as const).map((k) => (
              <li
                key={k}
                className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1"
              >
                {t(`${ns}.hero.${k}`)}
              </li>
            ))}
          </ul>
          <div className="flex w-full flex-col items-stretch gap-3 pt-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center">
            <a
              href="#ai-store"
              className="storefront-cta-primary inline-flex min-h-[48px] items-center justify-center rounded-2xl bg-emerald-500 px-7 py-3.5 text-sm font-bold text-black shadow-[0_0_40px_-6px_rgba(16,185,129,0.45)] hover:brightness-110"
            >
              {t("aiStore.cta", { defaultValue: "Create online shop →" })}
            </a>
            <a
              href="#website-services"
              className="inline-flex min-h-[44px] items-center justify-center rounded-2xl border border-white/20 px-6 py-3 text-sm font-semibold text-white hover:bg-white/5"
            >
              {t(`${ns}.cta.tryFree`, { defaultValue: "Open catalog" })}
            </a>
            <Link
              href="/kontakt"
              className="inline-flex min-h-[44px] items-center justify-center text-sm font-medium text-genesis-muted hover:text-white"
            >
              {t(`${ns}.cta.contact`, { defaultValue: "Contact" })}
            </Link>
          </div>
          <p className="text-[11px] leading-relaxed text-zinc-500">
            {t(`${ns}.ki.short`, {
              defaultValue:
                "Content and deliverables are AI-assisted. You can request edits after purchase.",
            })}{" "}
            <Link href="/ai-disclaimer" className="text-genesis-purple hover:underline">
              {t(`${ns}.ki.link`, { defaultValue: "AI notice (DE)" })}
            </Link>
          </p>
          <div className="mx-auto max-w-md pt-2">{marketSelect}</div>
        </div>
      </section>

      {/* Story */}
      <section id="story" className="mx-auto max-w-3xl space-y-8 scroll-mt-24">
        <div className="text-center space-y-3">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.story.title`, { defaultValue: "Opened a business in Germany?" })}
          </h2>
          <p className="text-sm text-genesis-muted sm:text-base">
            {t(`${ns}.story.subtitle`, {
              defaultValue: "We help with the next step — not another generic agency pitch.",
            })}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {(
            [
              ["story.problem1", "Impressum · Datenschutz · Wix?"],
              ["story.problem2", "Who answers clients at night?"],
              ["story.problem3", "Instagram · WhatsApp · Telegram?"],
            ] as const
          ).map(([key, fallback]) => (
            <article
              key={key}
              className="rounded-2xl border border-rose-500/20 bg-rose-950/20 p-4 text-sm text-rose-100/90"
            >
              <span className="text-rose-300" aria-hidden>
                ✕{" "}
              </span>
              {t(`${ns}.${key}`, { defaultValue: fallback })}
            </article>
          ))}
        </div>
        <div className="rounded-2xl border border-genesis-purple/40 bg-gradient-to-br from-genesis-purple/15 to-transparent p-6 text-center sm:p-8">
          <p className="text-xs uppercase tracking-[0.3em] text-genesis-purple">
            {BRAND_NAME}
          </p>
          <p className="mt-3 text-lg text-white sm:text-xl">
            {t(`${ns}.story.resolve`, {
              defaultValue: "Connect modules. AI handles the routine. You run the craft.",
            })}
          </p>
        </div>
      </section>

      {/* Core offer — Website · Store · Assistant · Audit */}
      <section id="modules" className="scroll-mt-24 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.modules.title`, { defaultValue: "What do you need for your business?" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.modules.subtitle`, {
              defaultValue: "Four clear products. No duplicate AI cards.",
            })}
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STORE_MODULES_PRIMARY.map(renderModuleCard)}
        </div>
        <div className="pt-4">
          <p className="mb-3 text-center text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            {t(`${ns}.modules.soonTitle`, { defaultValue: "Coming soon" })}
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {STORE_MODULES_SOON.map(renderModuleCard)}
          </div>
        </div>
      </section>

      {/* Beispiele — production SSOT (Vercel genesis-ai-engine.vercel.app) */}
      <section id="examples" className="scroll-mt-24 mx-auto max-w-4xl space-y-5">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.examples.title`, { defaultValue: "Beispiele" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.examples.subtitle`, {
              defaultValue:
                "Demo-Projekte aus der AI Factory. Echte Kundenprojekte erscheinen später als «Zuletzt veröffentlicht».",
            })}
          </p>
        </div>
        <ul className="grid gap-3 sm:grid-cols-2">
          {(
            [
              {
                id: "dental",
                emoji: "🦷",
                labelKey: "examples.dental",
                fallback: "Zahnarztpraxis",
                href: "/package-previews/sites/business/dental/index.html",
                kind: "website" as const,
              },
              {
                id: "law",
                emoji: "⚖️",
                labelKey: "examples.law",
                fallback: "Law office",
                href: "/package-previews/sites/business/law/index.html",
                kind: "website" as const,
              },
              {
                id: "restaurant",
                emoji: "🍽",
                labelKey: "examples.restaurant",
                fallback: "Restaurant",
                href: "/package-previews/sites/business/restaurant/index.html",
                kind: "website" as const,
              },
              {
                id: "beauty",
                emoji: "💄",
                labelKey: "examples.beauty",
                fallback: "Beauty / Fashion",
                href: "/package-previews/sites/business/beauty/index.html",
                kind: "website" as const,
              },
              {
                id: "auto",
                emoji: "🚗",
                labelKey: "examples.auto",
                fallback: "Handwerk / Auto",
                href: "/package-previews/sites/business/auto/index.html",
                kind: "website" as const,
              },
              {
                id: "fitness",
                emoji: "🏋️",
                labelKey: "examples.fitness",
                fallback: "Fitness club",
                href: "/package-previews/sites/business/fitness/index.html",
                kind: "website" as const,
              },
              {
                id: "handwerk",
                emoji: "🔨",
                labelKey: "examples.handwerk",
                fallback: "Handwerk",
                href: "/package-previews/sites/business/handwerk/index.html",
                kind: "website" as const,
              },
              {
                id: "it",
                emoji: "💻",
                labelKey: "examples.it",
                fallback: "IT company",
                href: "/package-previews/sites/business/it/index.html",
                kind: "website" as const,
              },
              {
                id: "store",
                emoji: "🛒",
                labelKey: "examples.store",
                fallback: "AI Store Demo",
                href: "/package-previews/stores/fashion/index.html",
                kind: "store" as const,
              },
              {
                id: "store-electronics",
                emoji: "🔌",
                labelKey: "examples.storeElectronics",
                fallback: "AI Store · Electronics",
                href: "/package-previews/stores/electronics/index.html",
                kind: "store" as const,
              },
            ] as const
          ).map((ex) => (
            <li key={ex.id}>
              <a
                href={ex.href}
                target={ex.kind === "website" ? "_blank" : undefined}
                rel={ex.kind === "website" ? "noopener noreferrer" : undefined}
                className="flex items-center justify-between gap-3 border-b border-white/10 py-3 text-left hover:border-emerald-500/40"
              >
                <span className="text-sm font-medium text-white">
                  <span className="mr-2" aria-hidden>
                    {ex.emoji}
                  </span>
                  {t(`${ns}.${ex.labelKey}`, { defaultValue: ex.fallback })}
                </span>
                <span className="shrink-0 text-xs font-semibold text-emerald-300">
                  {t(`${ns}.examples.view`, { defaultValue: "Ansehen →" })}
                </span>
              </a>
            </li>
          ))}
        </ul>
      </section>

      {/* Additional services — for existing websites */}
      <section id="website-services" className="scroll-mt-24 space-y-4">
        <ServiceCatalogGrid mode="agency" market={market} />
      </section>

      {/* AI Store highlight — plain language */}
      <section
        id="ai-store"
        className="scroll-mt-24 rounded-[2rem] border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-black/20 to-genesis-panel p-6 sm:p-8"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-200/80">
          {t("aiStore.badge", { defaultValue: "Online Store" })}
        </p>
        <h2 className="mt-3 text-2xl font-semibold text-white sm:text-3xl">
          {t("aiStore.landingTitle", {
            defaultValue: "Professional online shop for your business",
          })}
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-zinc-300">
          {t("aiStore.landingBody", {
            defaultValue:
              "After payment we automatically create a professional online store for your niche. The finished project appears in your client cabinet — open it, regenerate, or roll back versions. From 799 €.",
          })}
        </p>
        <ul className="mt-4 grid gap-2 text-sm text-zinc-400 sm:grid-cols-2">
          <li>
            ✓{" "}
            {t("aiStore.benefit1", {
              defaultValue: "Brief tailored to your catalog & shipping",
            })}
          </li>
          <li>
            ✓{" "}
            {t("aiStore.benefit2", {
              defaultValue: "Published storefront in your cabinet after pay",
            })}
          </li>
          <li>
            ✓{" "}
            {t("aiStore.benefit3", {
              defaultValue: "Open Store button — real HTML, not a fake demo",
            })}
          </li>
          <li>
            ✓{" "}
            {t("aiStore.benefit4", {
              defaultValue: "Regenerate and rollback versions when you need",
            })}
          </li>
        </ul>
        <Link
          href={`/order/shop?market=${encodeURIComponent(market)}`}
          className="storefront-cta-primary mt-6 inline-flex rounded-2xl bg-emerald-500 px-6 py-3 text-sm font-bold text-black hover:brightness-110"
        >
          {t("aiStore.cta", { defaultValue: "Create online shop →" })}
        </Link>
      </section>

      {/* Pricing — same EUR as /order checkout */}
      <section id="pricing" className="scroll-mt-24 space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.pricing.title`, { defaultValue: "Pricing" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.pricing.subtitle`, {
              defaultValue: "Paid packages — identical amounts on the order page.",
            })}
          </p>
          <p className="text-[11px] font-medium uppercase tracking-wider text-emerald-300/90">
            {t(`${ns}.pricing.paidBadge`, {
              defaultValue: "Real checkout prices · not a demo",
            })}
          </p>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-genesis-purple">
            {t(`${ns}.pricing.websites`, { defaultValue: "Website" })}
          </h3>
          <div className="grid gap-3 sm:grid-cols-3">
            {websiteTiers.map((tier) => (
              <article
                key={tier.id}
                className={`flex flex-col rounded-3xl border p-5 ${
                  tier.featured
                    ? "border-genesis-purple/50 bg-genesis-purple/10"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                <p className="text-sm text-zinc-300">{tier.name}</p>
                <p className="mt-2 text-3xl font-semibold text-white">{tier.priceLabel}</p>
                <p className="mt-0.5 text-[11px] text-zinc-500">
                  {t(`${ns}.pricing.oneTime`, { defaultValue: "One-time · paid checkout" })}
                </p>
                {"blurbKey" in tier && tier.blurbKey ? (
                  <p className="mt-2 flex-1 text-sm text-genesis-muted">
                    {t(`${ns}.${tier.blurbKey}`)}
                  </p>
                ) : (
                  <p className="mt-2 flex-1 text-sm text-genesis-muted">
                    {t(`${ns}.pricing.webCheckoutNote`, {
                      defaultValue: "One-time · same price at checkout.",
                    })}
                  </p>
                )}
                <Link
                  href={orderHrefFor(tier.id)}
                  onClick={() => logCommerceEvent("tier_select", tier.id, "site")}
                  className="mt-4 inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  {t(`${ns}.pricing.order`, { defaultValue: "Order" })}
                </Link>
              </article>
            ))}
          </div>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-genesis-purple">
            {t(`${ns}.pricing.chatbots`, { defaultValue: "AI Chatbot" })}
          </h3>
          <p className="mb-3 text-xs text-zinc-400">
            {t(`${ns}.pricing.botDisclaimer`, {
              defaultValue:
                "Setup + monthly. You pay for results: answers, leads, bookings — not for a list of apps.",
            })}
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {botTiers.map((tier) => (
              <article
                key={tier.id}
                className={`flex flex-col rounded-3xl border p-5 ${
                  tier.featured
                    ? "border-genesis-purple/50 bg-genesis-purple/10"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                <p className="text-sm text-zinc-300">{tier.name}</p>
                <p className="mt-2 text-3xl font-semibold text-white">{tier.setupLabel}</p>
                {tier.monthlyLabel ? (
                  <p className="mt-1 text-sm text-emerald-300/90">
                    {t(`${ns}.pricing.thenMonthly`, {
                      defaultValue: "then {{monthly}}/mo",
                      monthly: tier.monthlyLabel,
                    })}
                  </p>
                ) : null}
                {"blurbKey" in tier && tier.blurbKey ? (
                  <p className="mt-3 text-sm font-medium text-white/90">
                    {t(`${ns}.${tier.blurbKey}`)}
                  </p>
                ) : null}
                {"outcomeKeys" in tier && tier.outcomeKeys?.length ? (
                  <ul className="mt-3 flex-1 space-y-1.5 text-sm text-zinc-300">
                    {tier.outcomeKeys.map((key) => (
                      <li key={key} className="flex gap-2">
                        <span className="text-emerald-400" aria-hidden>
                          ✓
                        </span>
                        <span>{t(`${ns}.${key}`)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 flex-1 text-sm text-genesis-muted">
                    {t(`${ns}.pricing.botCheckoutNote`, {
                      defaultValue:
                        "Answers clients 24/7 and collects leads without a manager on shift.",
                    })}
                  </p>
                )}
                <p className="mt-3 text-[11px] text-zinc-500">
                  {t(`${ns}.pricing.botChannelsHonest`, {
                    defaultValue:
                      "Live today: Telegram. Website Chat / WhatsApp / Instagram — coming soon.",
                  })}
                </p>
                <Link
                  href={botHref(tier.id)}
                  onClick={() => logCommerceEvent("tier_select", tier.id, "site")}
                  className="mt-4 inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  {t(`${ns}.pricing.order`, { defaultValue: "Order" })}
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Why + counters */}
      <section className="space-y-6 text-center">
        <h2 className="text-2xl font-semibold text-white sm:text-3xl">
          {t(`${ns}.why.title`, { defaultValue: "Why entrepreneurs choose Virtus Core" })}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {(
            [
              ["why.statModules", "Modules"],
              ["why.statMarkets", "Markets"],
              ["why.statSupport", "Support"],
              ["why.statAi", "AI-assisted"],
            ] as const
          ).map(([key, fb]) => (
            <div
              key={key}
              className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-5"
            >
              <p className="text-lg font-semibold text-genesis-purple sm:text-xl">
                {t(`${ns}.${key}Value`)}
              </p>
              <p className="mt-1 text-xs text-genesis-muted">
                {t(`${ns}.${key}`, { defaultValue: fb })}
              </p>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-zinc-600">
          {t(`${ns}.why.illustrative`, {
            defaultValue: "Platform capabilities — not invented client revenue.",
          })}
        </p>
      </section>

      {/* Reviews + leave review */}
      <section
        id="reviews"
        className="rounded-[2rem] border border-amber-500/25 bg-gradient-to-br from-amber-950/20 via-black/20 to-genesis-panel p-6 sm:p-8"
      >
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 className="text-lg font-semibold text-white sm:text-xl">
            {t("reviews.title")}
          </h2>
          <Link
            href="/trust"
            className="rounded-xl border border-amber-400/30 bg-amber-950/40 px-4 py-2 text-xs font-semibold text-amber-100 hover:bg-amber-900/40"
          >
            {t(`${ns}.reviews.leave`, { defaultValue: "Leave a review" })}
          </Link>
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
                <p className="text-amber-300">
                  {"★".repeat(Math.max(1, Math.min(5, r.stars)))}
                </p>
                <p className="mt-2 text-white/85">«{r.text}»</p>
                <p className="mt-2 text-[11px] text-genesis-muted">
                  {[r.company_display_name, r.service_label].filter(Boolean).join(" · ") ||
                    t("reviews.client", { defaultValue: "Client" })}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Account + edits promise */}
      <section className="mx-auto max-w-2xl space-y-4 text-center text-sm text-genesis-muted">
        <p>
          {t(`${ns}.edits`, {
            defaultValue:
              "After purchase you can request edits to sites, bots and other modules via your client office.",
          })}
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/client/register" className="text-genesis-purple hover:underline">
            {t("s0.createAccount", { defaultValue: "Create account" })}
          </Link>
          <Link href="/client/login" className="hover:underline">
            {t("s0.signIn", { defaultValue: "Sign in" })}
          </Link>
          <Link href="/api-access" className="hover:underline">
            Platform API
          </Link>
        </div>
        <nav
          className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-[11px] text-zinc-500"
          aria-label="Legal"
        >
          <Link href="/impressum" className="hover:text-zinc-300 hover:underline">
            Impressum
          </Link>
          <Link href="/datenschutz" className="hover:text-zinc-300 hover:underline">
            Datenschutz
          </Link>
          <Link href="/ai-disclaimer" className="hover:text-zinc-300 hover:underline">
            {t(`${ns}.ki.link`, { defaultValue: "AI notice" })}
          </Link>
          <Link href="/kontakt" className="hover:text-zinc-300 hover:underline">
            {t(`${ns}.cta.contact`, { defaultValue: "Contact" })}
          </Link>
        </nav>
        <p className="text-[11px] text-zinc-600">
          {t(`${ns}.marketNote`, {
            defaultValue: "Market",
            market,
          })}
          {": "}
          {market}
        </p>
      </section>
    </div>
  );
}
