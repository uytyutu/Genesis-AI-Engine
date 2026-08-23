"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { BRAND_NAME } from "../../lib/publicBrand";
import { formatLocalizedMoney } from "../../lib/formatEur";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import { LiveActivityCanvas } from "./LiveActivityCanvas";
import {
  CHATBOT_PRICE_TIERS,
  STORE_MODULES_PRIMARY,
  WEBSITE_COMPARE_ROWS,
  WEBSITE_PRICE_TIERS,
  type StoreModule,
} from "./modules";
import {
  PACKAGE_EXAMPLE_COUNT,
  PUBLIC_VITRINE_STORES_BASIC,
  PUBLIC_VITRINE_STORES_BUSINESS,
  PUBLIC_VITRINE_STORES_PREMIUM,
  PUBLIC_VITRINE_WEBSITES_BASIC,
  PUBLIC_VITRINE_WEBSITES_BUSINESS,
  PUBLIC_VITRINE_WEBSITES_PREMIUM,
  STORE_PACKAGE_INCLUDES,
  WEBSITE_PACKAGE_INCLUDES,
  type PackageIncludesBlock,
  type PublicVitrineDemo,
} from "../../lib/publicVitrineCatalog";
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

function packageTitle(block: PackageIncludesBlock): string {
  const name =
    block.packageId === "basic"
      ? "Basic"
      : block.packageId === "business"
        ? "Business"
        : "Premium";
  const kind = block.kind === "website" ? "Website" : "Online-Shop";
  return `${kind} · ${name} · ${block.priceLabel}`;
}

function PackageExamplesBlock({
  ns,
  t,
  block,
  demos,
  orderHref,
  onOrder,
  exampleCount,
}: {
  ns: string;
  t: (key: string, opts?: { defaultValue?: string }) => string;
  block: PackageIncludesBlock;
  demos: PublicVitrineDemo[];
  orderHref: string;
  onOrder: () => void;
  exampleCount: number;
}) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-300/90">
            {block.packageId}
          </p>
          <h4 className="mt-1 text-xl font-semibold text-white">{packageTitle(block)}</h4>
          <p className="mt-1 text-xs text-genesis-muted">
            {exampleCount}{" "}
            {t(`${ns}.examples.equalCount`, {
              defaultValue: "Beispiele — gleiche Branchen in jedem Paket",
            })}
          </p>
        </div>
        <Link
          href={orderHref}
          onClick={onOrder}
          className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
        >
          {t(`${ns}.pricing.orderNow`, { defaultValue: "Jetzt bestellen" })}
        </Link>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            {t(`${ns}.examples.includesTitle`, { defaultValue: "Was enthalten ist" })}
          </p>
          <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
            {block.includes.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="text-emerald-400" aria-hidden>
                  ✓
                </span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            {block.virtusControl
              ? t(`${ns}.examples.controlTitle`, {
                  defaultValue: "Virtus Steuerung",
                })
              : t(`${ns}.examples.controlBasicTitle`, {
                  defaultValue: "Steuerung",
                })}
          </p>
          <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
            {block.controlLines.map((line) => (
              <li key={line} className="flex gap-2">
                <span className={block.virtusControl ? "text-amber-300" : "text-zinc-500"} aria-hidden>
                  {block.virtusControl ? "⚙" : "—"}
                </span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
          {block.virtusControl ? (
            <p className="mt-2 text-xs text-amber-200/80">
              {t(`${ns}.examples.controlNote`, {
                defaultValue:
                  "Nach dem Kauf: Client Workspace — Produkte, Preise, Medien, Texte, Versionen. Buttons im Panel sind echte Aktionen (nicht Dekoration).",
              })}
            </p>
          ) : null}
        </div>
      </div>

      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {demos.map((ex) => (
          <li key={ex.id}>
            <a
              href={ex.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-3 py-2.5 text-left transition hover:border-emerald-500/40"
            >
              <span>
                <span className="text-sm font-medium text-white">
                  <span className="mr-1.5" aria-hidden>
                    {ex.emoji}
                  </span>
                  {t(`${ns}.${ex.labelKey}`, { defaultValue: ex.fallback })}
                </span>
                <span className="mt-0.5 block text-xs text-genesis-muted">
                  {ex.badge} · {ex.blurb}
                </span>
              </span>
              <span className="shrink-0 text-xs font-semibold text-emerald-300">
                {t(`${ns}.examples.view`, { defaultValue: "Ansehen →" })}
              </span>
            </a>
          </li>
        ))}
      </ul>
    </article>
  );
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
  packages: _packages,
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
  void _packages;

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

  // Storefront display matches live beta (Basic 199 · Business 399 · Premium 699).
  // Sales API may return Standalone/Connected 499 — do not let that rewrite the public cards.
  const websiteTiers = WEBSITE_PRICE_TIERS.map((tier) => ({
    id: tier.id,
    priceLabel: formatLocalizedMoney(tier.priceEur, "EUR", localeTag),
    name: t(`${ns}.${tier.nameKey}`),
    featured: "featured" in tier && Boolean(tier.featured),
    blurbKey: tier.blurbKey,
    featureKeys: tier.featureKeys,
  }));

  const compareCell = (value: string) => {
    if (value === "yes") {
      return (
        <span className="text-emerald-400" aria-label="yes">
          ✓
        </span>
      );
    }
    if (value === "no") {
      return (
        <span className="text-zinc-600" aria-label="no">
          —
        </span>
      );
    }
    const valKey =
      value === "pages5"
        ? "pricing.compareVal_pages5"
        : value === "pagesMulti"
          ? "pricing.compareVal_pagesMulti"
          : value === "pagesExtra"
            ? "pricing.compareVal_pagesExtra"
            : value === "seoPro"
              ? "pricing.compareVal_seoPro"
              : null;
    return (
      <span className="text-xs font-medium text-emerald-200/90">
        {valKey ? t(`${ns}.${valKey}`) : value}
      </span>
    );
  };

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
      {/* Hero — match live beta (line1 + emotion + prices + dual CTAs; no line2) */}
      <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/20 px-4 py-10 shadow-[0_0_80px_-24px_rgba(16,185,129,0.25)] backdrop-blur-md sm:rounded-[2rem] sm:px-10 sm:py-14">
        <LiveActivityCanvas />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-emerald-950/10 via-transparent to-black/40" aria-hidden />
        <div className="relative z-10 mx-auto max-w-3xl space-y-5 text-center sm:space-y-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-emerald-400">
            {BRAND_NAME}
          </p>
          <h1 className="text-[1.75rem] font-bold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl">
            {t(`${ns}.hero.line1`, {
              defaultValue:
                "Wir erstellen professionelle Websites, Online-Shops und AI-Lösungen für Unternehmen.",
            })}
          </h1>
          <p className="mx-auto max-w-xl text-base font-medium text-white/90 sm:text-lg">
            {t(`${ns}.hero.emotion`, {
              defaultValue:
                "Klare Preise. Schnelle Lieferung. Sie veröffentlichen und steuern alles in Virtus Core — nicht wie bei einer klassischen Web-Agentur.",
            })}
          </p>
          <p className="text-sm font-semibold text-white sm:text-base">
            {t(`${ns}.hero.pricesLine`, {
              defaultValue: "Website 199–699 € · AI Store ab 799 €",
            })}
          </p>
          <div className="flex w-full flex-col items-stretch gap-3 pt-1 sm:flex-row sm:items-center sm:justify-center">
            <Link
              href="#pricing"
              className="storefront-cta-primary inline-flex min-h-[48px] items-center justify-center rounded-2xl bg-emerald-500 px-7 py-3.5 text-sm font-bold text-black shadow-[0_0_40px_-6px_rgba(16,185,129,0.45)] hover:brightness-110"
            >
              {t(`${ns}.hero.ctaWebsite`, { defaultValue: "🌐 Website bestellen" })}
            </Link>
            <a
              href="#ai-store"
              className="inline-flex min-h-[48px] items-center justify-center rounded-2xl border border-white/25 px-7 py-3.5 text-sm font-bold text-white hover:bg-white/5"
            >
              {t(`${ns}.hero.ctaStore`, { defaultValue: "🛒 AI Store bestellen" })}
            </a>
          </div>
          <p className="text-[11px] leading-relaxed text-zinc-500">
            {t(`${ns}.ki.short`, {
              defaultValue:
                "Inhalte und Lieferungen werden KI-gestützt erstellt. Nach dem Kauf können Sie Änderungen anfordern.",
            })}{" "}
            <Link href="/ai-disclaimer" className="text-emerald-400 hover:underline">
              {t(`${ns}.ki.link`, { defaultValue: "KI-Hinweis" })}
            </Link>
          </p>
          <div className="mx-auto max-w-md pt-2">{marketSelect}</div>
        </div>
      </section>

      {/* Website oder AI Store — live beta first content section */}
      <section id="path" className="mx-auto max-w-4xl space-y-5 scroll-mt-24">
        <h2 className="text-center text-2xl font-semibold text-white sm:text-3xl">
          {t(`${ns}.diff.title`, { defaultValue: "Website oder AI Store?" })}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-300/90">
            {t(`${ns}.diff.webLabel`, { defaultValue: "Website" })}
          </p>
          <h3 className="mt-2 text-xl font-semibold text-white">
            {t(`${ns}.diff.webHeadline`, { defaultValue: "Präsentiert Ihr Unternehmen." })}
          </h3>
          <p className="mt-2 text-sm text-genesis-muted">
            {t(`${ns}.diff.webBody`, {
              defaultValue:
                "Seiten, Kontaktweg, Impressum — Besucher verstehen, wer Sie sind und wie sie Sie erreichen. Ab 199 €.",
            })}
          </p>
          <a
            href="#pricing"
            className="mt-4 inline-flex text-sm font-semibold text-emerald-300 hover:underline"
          >
            {t(`${ns}.diff.webCta`, { defaultValue: "Website-Pakete ansehen →" })}
          </a>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-300/90">
            {t(`${ns}.diff.storeLabel`, { defaultValue: "AI Store" })}
          </p>
          <h3 className="mt-2 text-xl font-semibold text-white">
            {t(`${ns}.diff.storeHeadline`, {
              defaultValue: "Hilft, Produkte zu verkaufen und den Online-Shop zu führen.",
            })}
          </h3>
          <p className="mt-2 text-sm text-genesis-muted">
            {t(`${ns}.diff.storeBody`, {
              defaultValue:
                "Katalog, Warenkorb, Admin und Käuferkonto — Stripe, Versand und E-Mail über Ihre eigenen Konten anbindbar. Ab 799 €.",
            })}
          </p>
          <a
            href="#ai-store"
            className="mt-4 inline-flex text-sm font-semibold text-emerald-300 hover:underline"
          >
            {t(`${ns}.diff.storeCta`, { defaultValue: "AI Store ansehen →" })}
          </a>
        </div>
        </div>
      </section>

      {/* Story section omitted on public /site — not present on live beta first flow */}

      {/* Beispiele — grouped by PACKAGE; equal niche count per tier */}
      <section id="examples" className="scroll-mt-24 mx-auto max-w-4xl space-y-10">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.examples.title`, { defaultValue: "Beispiele nach Paket" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.examples.subtitle`, {
              defaultValue:
                "Pro Paket: was enthalten ist + dieselben Branchen-Beispiele. Basic ohne Panel — ab Business mit Virtus Steuerung.",
            })}
          </p>
        </div>

        {(
          [
            {
              kind: "website" as const,
              titleKey: "examples.websitesTitle",
              titleFallback: "Website-Pakete & Beispiele",
              packages: [
                {
                  block: WEBSITE_PACKAGE_INCLUDES[0],
                  demos: PUBLIC_VITRINE_WEBSITES_BASIC,
                  orderId: "basic",
                },
                {
                  block: WEBSITE_PACKAGE_INCLUDES[1],
                  demos: PUBLIC_VITRINE_WEBSITES_BUSINESS,
                  orderId: "business",
                },
                {
                  block: WEBSITE_PACKAGE_INCLUDES[2],
                  demos: PUBLIC_VITRINE_WEBSITES_PREMIUM,
                  orderId: "premium",
                },
              ],
            },
            {
              kind: "store" as const,
              titleKey: "examples.shopsTitle",
              titleFallback: "Online-Shop-Pakete & Beispiele",
              packages: [
                {
                  block: STORE_PACKAGE_INCLUDES[0],
                  demos: PUBLIC_VITRINE_STORES_BASIC,
                  orderId: "basic",
                },
                {
                  block: STORE_PACKAGE_INCLUDES[1],
                  demos: PUBLIC_VITRINE_STORES_BUSINESS,
                  orderId: "business",
                },
                {
                  block: STORE_PACKAGE_INCLUDES[2],
                  demos: PUBLIC_VITRINE_STORES_PREMIUM,
                  orderId: "premium",
                },
              ],
            },
          ] as const
        ).map((group) => (
          <div key={group.kind} className="space-y-6">
            <h3 className="text-left text-lg font-semibold text-white">
              {t(`${ns}.${group.titleKey}`, { defaultValue: group.titleFallback })}
            </h3>
            {group.packages.map(({ block, demos, orderId }) => (
              <PackageExamplesBlock
                key={`${group.kind}-${block.packageId}`}
                ns={ns}
                t={t}
                block={block}
                demos={demos}
                orderHref={
                  group.kind === "store"
                    ? `${orderHrefFor(orderId)}&type=shop`
                    : orderHrefFor(orderId)
                }
                onOrder={() =>
                  logCommerceEvent(
                    "tier_select",
                    block.packageId,
                    group.kind === "store" ? "store" : "site",
                  )
                }
                exampleCount={
                  demos.filter((d) => !(d.badge || "").includes("Cinematic")).length ||
                  PACKAGE_EXAMPLE_COUNT
                }
              />
            ))}
          </div>
        ))}
      </section>

      {/* So läuft die Arbeit — live beta order after Beispiele */}
      <section id="how-it-works" className="scroll-mt-24 mx-auto max-w-3xl space-y-5">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.how.title`, { defaultValue: "So läuft die Arbeit" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.how.subtitle`, {
              defaultValue:
                "Ein klarer Weg von der Bestellung bis zur Veröffentlichung — damit Sie wissen, was nach der Zahlung passiert.",
            })}
          </p>
        </div>
        <ol className="space-y-3">
          {(
            [
              "how.step1",
              "how.step2",
              "how.step3",
              "how.step4",
              "how.step5",
              "how.step6",
              "how.step7",
            ] as const
          ).map((key, i) => (
            <li
              key={key}
              className="flex gap-3 border-b border-white/10 pb-3 text-left last:border-0 last:pb-0"
            >
              <span className="mt-0.5 w-7 shrink-0 text-sm font-semibold text-emerald-300">
                {i + 1}.
              </span>
              <span className="text-sm text-zinc-200 sm:text-base">{t(`${ns}.${key}`)}</span>
            </li>
          ))}
        </ol>
      </section>

      {/* Website packages — before AI Store, matching live beta */}
      <section id="pricing" className="scroll-mt-24 space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.pricing.title`, { defaultValue: "Website-Pakete · was enthalten ist" })}
          </h2>
          <p className="text-sm text-genesis-muted">
            {t(`${ns}.pricing.subtitle`, {
              defaultValue:
                "Was Sie für 199 €, 399 € und 699 € bekommen — dieselben Beträge im Checkout.",
            })}
          </p>
          <p className="text-sm text-zinc-300">
            {t(`${ns}.pricing.afterPay`, {
              defaultValue:
                "Nach der Zahlung: AI Factory erstellt die Website → Sie prüfen → veröffentlichen. Oft in etwa 15–30 Minuten fertig.",
            })}
          </p>
        </div>

        <div>
          <div className="grid gap-3 sm:grid-cols-3">
            {websiteTiers.map((tier) => (
              <article
                key={tier.id}
                className={`flex flex-col rounded-3xl border p-5 ${
                  tier.featured
                    ? "border-emerald-500/40 bg-emerald-950/20"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                <p className="text-sm text-zinc-300">{tier.name}</p>
                <p className="mt-2 text-3xl font-semibold text-white">{tier.priceLabel}</p>
                <p className="mt-0.5 text-[11px] text-zinc-500">
                  {t(`${ns}.pricing.oneTime`, { defaultValue: "Einmalig · Checkout" })}
                </p>
                {"blurbKey" in tier && tier.blurbKey ? (
                  <p className="mt-2 text-sm text-genesis-muted">{t(`${ns}.${tier.blurbKey}`)}</p>
                ) : null}
                <ul className="mt-3 flex-1 space-y-1.5 text-sm text-zinc-300">
                  {tier.featureKeys.map((key) => (
                    <li key={key} className="flex gap-2">
                      <span className="text-emerald-400" aria-hidden>
                        ✓
                      </span>
                      <span>{t(`${ns}.${key}`)}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={orderHrefFor(tier.id)}
                  onClick={() => logCommerceEvent("tier_select", tier.id, "site")}
                  className="mt-4 inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  {t(`${ns}.pricing.orderNow`, { defaultValue: "Jetzt bestellen" })}
                </Link>
              </article>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full min-w-[36rem] border-collapse text-left text-sm">
            <caption className="sr-only">
              {t(`${ns}.pricing.compareTitle`, { defaultValue: "Website-Pakete im Vergleich" })}
            </caption>
            <thead>
              <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-zinc-400">
                <th className="px-4 py-3 font-semibold">
                  {t(`${ns}.pricing.compareFeature`, { defaultValue: "Funktion" })}
                </th>
                <th className="px-3 py-3 text-center font-semibold text-white">Basic</th>
                <th className="px-3 py-3 text-center font-semibold text-emerald-200">Business</th>
                <th className="px-3 py-3 text-center font-semibold text-white">Premium</th>
              </tr>
            </thead>
            <tbody>
              {WEBSITE_COMPARE_ROWS.map((row) => (
                <tr key={row.labelKey} className="border-b border-white/5">
                  <th scope="row" className="px-4 py-2.5 font-medium text-zinc-300">
                    {t(`${ns}.${row.labelKey}`)}
                  </th>
                  <td className="px-3 py-2.5 text-center">{compareCell(row.basic)}</td>
                  <td className="bg-emerald-950/20 px-3 py-2.5 text-center">
                    {compareCell(row.business)}
                  </td>
                  <td className="px-3 py-2.5 text-center">{compareCell(row.premium)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* AI Store — after website packages (live beta order) */}
      <section
        id="ai-store"
        className="scroll-mt-24 space-y-6 rounded-[2rem] border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-black/20 to-genesis-panel p-6 sm:p-8"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-200/80">
            {t("aiStore.badge", { defaultValue: "AI Store" })}
          </p>
          <h2 className="mt-3 text-2xl font-semibold text-white sm:text-3xl">
            {t("aiStore.landingTitle")}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-zinc-300">{t("aiStore.landingBody")}</p>
          <p className="mt-3 max-w-3xl text-sm text-zinc-400">{t("aiStore.whyMore")}</p>
        </div>
        <ul className="grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
          {(
            [
              "valueAdmin",
              "valueBuyers",
              "valueProducts",
              "valueStripe",
              "valueShipping",
              "valueTaxes",
              "valueAnalytics",
              "valueVector",
            ] as const
          ).map((key) => (
            <li key={key} className="flex gap-2">
              <span className="text-emerald-400" aria-hidden>
                ✓
              </span>
              <span>{t(`aiStore.${key}`)}</span>
            </li>
          ))}
        </ul>
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <p className="mb-2 text-sm font-semibold text-white">{t("aiStore.includedNowTitle")}</p>
            <ul className="space-y-1.5 text-sm text-zinc-300">
              {(
                [
                  "includedNow1",
                  "includedNow2",
                  "includedNow3",
                  "includedNow4",
                  "includedNow5",
                  "includedNow6",
                  "includedNow7",
                  "includedNow8",
                ] as const
              ).map((key) => (
                <li key={key} className="flex gap-2">
                  <span className="text-emerald-400" aria-hidden>
                    ✓
                  </span>
                  <span>{t(`aiStore.${key}`)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-2 text-sm font-semibold text-white">{t("aiStore.connectOwnerTitle")}</p>
            <p className="mb-3 text-sm text-zinc-400">{t("aiStore.connectOwnerNote")}</p>
            <p className="text-sm text-zinc-300">
              Stripe · PayPal · SMTP · DHL · DPD · GLS · UPS · FedEx
            </p>
          </div>
        </div>
        <div>
          <p className="mb-2 text-sm font-semibold text-white">{t("aiStore.tiersTitle")}</p>
          <div className="grid gap-3 sm:grid-cols-3">
            <article className="rounded-2xl border border-emerald-500/35 bg-emerald-950/25 p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-200">
                {t("aiStore.tierStartBadge")}
              </p>
              <p className="mt-1 text-lg font-semibold text-white">{t("aiStore.tierStartName")}</p>
              <p className="mt-1 text-2xl font-bold text-white">{t("aiStore.tierStartPrice")}</p>
              <p className="mt-2 text-sm text-zinc-400">{t("aiStore.tierStartDesc")}</p>
              <Link
                href={`/order/shop?market=${encodeURIComponent(market)}`}
                className="storefront-cta-primary mt-4 inline-flex rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-bold text-black hover:brightness-110"
              >
                {t("aiStore.tierStartCta")}
              </Link>
            </article>
            <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 opacity-80">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                {t("aiStore.tierBusinessBadge")}
              </p>
              <p className="mt-1 text-lg font-semibold text-white">{t("aiStore.tierBusinessName")}</p>
              <p className="mt-1 text-2xl font-bold text-white">{t("aiStore.tierBusinessPrice")}</p>
              <p className="mt-2 text-sm text-zinc-400">{t("aiStore.tierBusinessDesc")}</p>
            </article>
            <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 opacity-80">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                {t("aiStore.tierPremiumBadge")}
              </p>
              <p className="mt-1 text-lg font-semibold text-white">{t("aiStore.tierPremiumName")}</p>
              <p className="mt-1 text-2xl font-bold text-white">{t("aiStore.tierPremiumPrice")}</p>
              <p className="mt-2 text-sm text-zinc-400">{t("aiStore.tierPremiumDesc")}</p>
            </article>
          </div>
        </div>
      </section>

      {/* AI Business Assistant — separate section on live beta */}
      <section id="digital-employee" className="scroll-mt-24 space-y-6">
        <div className="text-center space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-genesis-purple">
            {t(`${ns}.pricing.chatbots`, { defaultValue: "AI Chatbot" })}
          </p>
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.modules.assistant.name`, { defaultValue: "AI Business Assistant" })}
          </h2>
          <p className="mx-auto max-w-2xl text-sm text-genesis-muted">
            {t(`${ns}.pricing.botDisclaimer`)}
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {botTiers.map((tier) => (
            <article
              key={tier.id}
              className={`flex flex-col rounded-3xl border p-5 ${
                tier.featured
                  ? "border-emerald-500/40 bg-emerald-950/20"
                  : "border-white/10 bg-white/[0.03]"
              }`}
            >
              <p className="text-sm text-zinc-300">{tier.name}</p>
              <p className="mt-2 text-3xl font-semibold text-white">{tier.setupLabel}</p>
              {tier.monthlyLabel ? (
                <p className="mt-1 text-sm text-emerald-300/90">
                  {t(`${ns}.pricing.thenMonthly`, {
                    defaultValue: "danach {{monthly}}/Mon.",
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
              ) : null}
              <p className="mt-3 text-[11px] text-zinc-500">
                {t(`${ns}.pricing.botChannelsHonest`)}
              </p>
              <Link
                href={botHref(tier.id)}
                onClick={() => logCommerceEvent("tier_select", tier.id, "site")}
                className="mt-4 inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
              >
                {t(`${ns}.pricing.orderNow`, { defaultValue: "Jetzt bestellen" })}
              </Link>
            </article>
          ))}
        </div>
      </section>

      {/* Why Virtus — agency comparison table (live beta) */}
      <section id="why-virtus" className="scroll-mt-24 mx-auto max-w-3xl space-y-5">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.why.title`, { defaultValue: "Warum günstiger als Agenturen?" })}
          </h2>
          <p className="text-sm text-genesis-muted">{t(`${ns}.why.subtitle`)}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[28rem] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-white/15 text-xs uppercase tracking-wider text-zinc-400">
                <th className="px-3 py-3 font-semibold">{t(`${ns}.why.colAgency`)}</th>
                <th className="px-3 py-3 font-semibold text-emerald-200">
                  {t(`${ns}.why.colVirtus`)}
                </th>
              </tr>
            </thead>
            <tbody>
              {(
                [
                  ["why.rowPriceAgency", "why.rowPriceVirtus"],
                  ["why.rowWaitAgency", "why.rowWaitVirtus"],
                  ["why.rowEditsAgency", "why.rowEditsVirtus"],
                  ["why.rowStackAgency", "why.rowStackVirtus"],
                ] as const
              ).map(([agencyKey, virtusKey]) => (
                <tr key={agencyKey} className="border-b border-white/10">
                  <td className="px-3 py-3 text-zinc-400">{t(`${ns}.${agencyKey}`)}</td>
                  <td className="px-3 py-3 font-medium text-white">{t(`${ns}.${virtusKey}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-center text-[10px] text-zinc-600">{t(`${ns}.why.illustrative`)}</p>
        <p className="text-center text-sm">
          <Link href="/why" className="text-emerald-300 hover:underline">
            {t(`${ns}.why.pageLink`, { defaultValue: "Vollständiger Vergleich →" })}
          </Link>
        </p>
      </section>

      {/* Core offer — three live products (beta: no soon-row here) */}
      <section id="modules" className="scroll-mt-24 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-white sm:text-3xl">
            {t(`${ns}.modules.title`, { defaultValue: "Was braucht Ihr Unternehmen?" })}
          </h2>
          <p className="text-sm text-genesis-muted">{t(`${ns}.modules.subtitle`)}</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">{STORE_MODULES_PRIMARY.map(renderModuleCard)}</div>
      </section>

      {/* Additional services — after modules, matching live beta */}
      <section id="website-services" className="scroll-mt-24 space-y-4">
        <ServiceCatalogGrid mode="agency" market={market} />
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
