"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { formatLocalizedMoney } from "../../lib/formatEur";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import { LANDING_PACKAGES_EUR } from "../../lib/commercialCatalog";
import { CHATBOT_PRICE_TIERS } from "./modules";
import {
  shopShowcaseSlides,
  websiteShowcaseSlides,
} from "../../lib/vitrineShowcaseCatalog";
import { VirtusCoreDirectionsHero } from "./VirtusCoreDirectionsHero";
import {
  BotChatMock,
  OfficeDocsMock,
} from "./VitrineProductMocks";

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

/**
 * Commercial /site funnel only — sellable products, no roadmap / Live-Soon / ops jargon.
 * Structure: Hero → Available now → Office → Selected work → For business → Why → CTA
 */
export function CommercialAgencyHub({
  market,
  localeTag,
  marketSelect,
  reviews: _reviews,
  botPackages,
  onOpenWebsites: _onOpenWebsites,
  onOpenBots: _onOpenBots,
  onOpenAnalysis,
  orderHrefFor,
  botOrderHrefFor,
}: Props) {
  const { t } = useTranslation("site");
  const ns = "agencyHub";

  const websiteFrom = formatLocalizedMoney(LANDING_PACKAGES_EUR.basic, "EUR", localeTag);
  const shopFrom = formatLocalizedMoney(799, "EUR", localeTag);
  const botAnchor =
    botPackages?.find((p) => p.package_id === "bot_starter") || botPackages?.[0];
  const botSetup =
    botAnchor?.setup_label ||
    formatLocalizedMoney(CHATBOT_PRICE_TIERS[0].setupEur, "EUR", localeTag);
  const receptionistFrom = formatLocalizedMoney(499, "EUR", localeTag);
  const automationFrom = formatLocalizedMoney(650, "EUR", localeTag);
  const vectorFrom = formatLocalizedMoney(999, "EUR", localeTag);

  const shopHref = `/order/shop?market=${encodeURIComponent(market)}`;
  const botHref =
    botOrderHrefFor?.("bot_starter") ||
    `/order/bot?market=${encodeURIComponent(market)}&package=bot_starter`;
  const vectorHref =
    botOrderHrefFor?.("bot_business") ||
    `/order/bot?market=${encodeURIComponent(market)}&package=bot_business`;
  const automationHref = `/order/service/business_automation?market=${encodeURIComponent(
    market,
  )}&form=1`;
  const websiteOrderHref = orderHrefFor("business");
  const repairHref = `/order/service/website_repair?market=${encodeURIComponent(market)}&form=1`;

  const siteWork = websiteShowcaseSlides().slice(0, 4);
  const shopWork = shopShowcaseSlides()
    .filter((s, i, arr) => arr.findIndex((x) => x.href === s.href) === i)
    .slice(0, 3);

  const available = [
    {
      id: "websites",
      href: "/site/websites",
      orderHref: websiteOrderHref,
      title: t(`${ns}.available.websites`, { defaultValue: "Websites" }),
      blurb: t(`${ns}.available.websitesBlurb`, {
        defaultValue: "Professional site for your business, service or project.",
      }),
      gets: [
        t(`${ns}.available.webGet1`, { defaultValue: "Industry-ready design" }),
        t(`${ns}.available.webGet2`, { defaultValue: "Contact · Legal pages" }),
        t(`${ns}.available.webGet3`, { defaultValue: "Clear packages to order" }),
      ],
      price: t(`${ns}.available.fromPrice`, {
        defaultValue: "from {{price}}",
        price: websiteFrom,
      }),
      cta: t(`${ns}.available.websitesCta`, { defaultValue: "View websites" }),
      tone: "border-sky-400/30",
    },
    {
      id: "shops",
      href: "/site/shops",
      orderHref: shopHref,
      title: t(`${ns}.available.shops`, { defaultValue: "Online Shops" }),
      blurb: t(`${ns}.available.shopsBlurb`, {
        defaultValue: "Catalog, products, cart and shop admin — built to sell.",
      }),
      gets: [
        t(`${ns}.available.shopGet1`, { defaultValue: "Product catalog & cart" }),
        t(`${ns}.available.shopGet2`, { defaultValue: "Owner shop admin" }),
        t(`${ns}.available.shopGet3`, {
          defaultValue: "You connect Stripe & shipping",
        }),
      ],
      price: t(`${ns}.available.fromPrice`, {
        defaultValue: "from {{price}}",
        price: shopFrom,
      }),
      cta: t(`${ns}.available.shopsCta`, { defaultValue: "View shops" }),
      tone: "border-violet-400/30",
    },
    {
      id: "bots",
      href: "/site/bots",
      orderHref: botHref,
      title: t(`${ns}.available.bots`, { defaultValue: "AI Bots" }),
      blurb: t(`${ns}.available.botsBlurb`, {
        defaultValue: "Receptionist, support and sales for website chat & Telegram.",
      }),
      gets: [
        t(`${ns}.available.botGet1`, { defaultValue: "Qualifies inquiries" }),
        t(`${ns}.available.botGet2`, { defaultValue: "Ready leads for the owner" }),
        t(`${ns}.available.botGet3`, {
          defaultValue: "Telegram + website chat",
        }),
      ],
      price: t(`${ns}.available.fromPrice`, {
        defaultValue: "from {{price}}",
        price: botSetup,
      }),
      cta: t(`${ns}.available.botsCta`, { defaultValue: "View AI Bots" }),
      tone: "border-emerald-400/30",
    },
    {
      id: "office",
      href: "/office",
      orderHref: "/office",
      title: t(`${ns}.available.office`, { defaultValue: "Virtus Office" }),
      blurb: t(`${ns}.available.officeBlurb`, {
        defaultValue:
          "Digital office for documents, translations, calculations and work tasks.",
      }),
      gets: [
        t(`${ns}.available.offGet1`, { defaultValue: "Translate · OCR · convert" }),
        t(`${ns}.available.offGet2`, { defaultValue: "PDF · DOCX · Excel / CSV" }),
        t(`${ns}.available.offGet3`, {
          defaultValue: "Upload → Virtus proposes the task",
        }),
      ],
      price: t(`${ns}.available.officePrice`, {
        defaultValue: "from €4.90",
      }),
      cta: t(`${ns}.available.officeCta`, { defaultValue: "Open Virtus Office" }),
      tone: "border-sky-400/30",
    },
  ] as const;

  const officeCapabilities = [
    ["capTranslate", "🌍", "Translation — any supported language → your target"],
    ["capCreate", "📄", "Create letters, applications, CV, business documents"],
    ["capCalc", "🧮", "Calculations from your tables and numbers"],
    ["capAnalyze", "🔍", "Explain what the document is and what matters"],
    ["capLegal", "⚖️", "Official drafts — not a lawyer substitute"],
    ["capConvert", "🔄", "Convert PDF · DOCX · CSV · XLSX · OCR where supported"],
  ] as const;

  const smartSteps = [
    "smart1",
    "smart2",
    "smart3",
    "smart4",
    "smart5",
    "smart6",
    "smart7",
    "smart8",
  ] as const;

  const b2b = [
    {
      id: "receptionist",
      title: t(`${ns}.b2b.receptionistTitle`, { defaultValue: "AI Receptionist" }),
      forWhom: t(`${ns}.b2b.receptionistFor`, {
        defaultValue: "For: trades, local services, shops",
      }),
      does: t(`${ns}.b2b.receptionistDoes`, {
        defaultValue: "Takes inquiries → collects data → sends a qualified lead to you",
      }),
      price: t(`${ns}.b2b.fromPrice`, {
        defaultValue: "from {{price}}",
        price: receptionistFrom,
      }),
      href: botHref,
      cta: t(`${ns}.b2b.receptionistCta`, { defaultValue: "Order AI Receptionist" }),
      featured: true,
    },
    {
      id: "automation",
      title: t(`${ns}.b2b.automationTitle`, { defaultValue: "Business Automation" }),
      forWhom: t(`${ns}.b2b.automationFor`, {
        defaultValue: "For: repeating lead and follow-up processes",
      }),
      does: t(`${ns}.b2b.automationDoes`, {
        defaultValue: "Inquiry → qualify → task → follow-up — set up once for your flow",
      }),
      price: t(`${ns}.b2b.fromPrice`, {
        defaultValue: "from {{price}}",
        price: automationFrom,
      }),
      href: automationHref,
      cta: t(`${ns}.b2b.automationCta`, { defaultValue: "Request automation" }),
      featured: false,
    },
    {
      id: "vector",
      title: t(`${ns}.b2b.vectorTitle`, { defaultValue: "AI Employee / Vector" }),
      forWhom: t(`${ns}.b2b.vectorFor`, {
        defaultValue: "For: a defined business role with allowed actions",
      }),
      does: t(`${ns}.b2b.vectorDoes`, {
        defaultValue: "AI employee set up under your process — support, analysis, actions",
      }),
      price: t(`${ns}.b2b.fromPrice`, {
        defaultValue: "from {{price}}",
        price: vectorFrom,
      }),
      href: vectorHref,
      cta: t(`${ns}.b2b.vectorCta`, { defaultValue: "Order AI Employee" }),
      featured: false,
    },
  ];

  return (
    <div className="agency-hub relative space-y-16 sm:space-y-20">
      <VirtusCoreDirectionsHero marketSelect={marketSelect} />

      {/* AVAILABLE NOW */}
      <section id="available" className="scroll-mt-24 space-y-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.available.title`, { defaultValue: "What you can order today" })}
          </h2>
          <p className="mt-3 text-sm text-zinc-400 sm:text-base">
            {t(`${ns}.available.sub`, {
              defaultValue: "Clear products — what you get, from price, how to order.",
            })}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {available.map((item) => (
            <article
              key={item.id}
              className={`flex flex-col rounded-2xl border bg-white/[0.03] p-5 ${item.tone}`}
            >
              <h3 className="text-lg font-semibold text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-300">{item.blurb}</p>
              <ul className="mt-4 flex-1 space-y-1.5 text-xs text-zinc-400">
                {item.gets.map((g) => (
                  <li key={g} className="flex gap-2">
                    <span className="text-emerald-400" aria-hidden>
                      ✓
                    </span>
                    <span>{g}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm font-semibold text-white">{item.price}</p>
              <div className="mt-4 flex flex-col gap-2">
                <Link
                  href={item.href}
                  className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/20 px-4 text-sm font-semibold text-white hover:bg-white/[0.05]"
                >
                  {item.cta}
                </Link>
                <Link
                  href={item.orderHref}
                  onClick={() =>
                    logCommerceEvent("tier_select", `available_${item.id}`, "site")
                  }
                  className="inline-flex min-h-[44px] items-center justify-center rounded-xl bg-violet-600 px-4 text-sm font-semibold text-white hover:bg-violet-500"
                >
                  {t(`${ns}.available.order`, { defaultValue: "Order →" })}
                </Link>
              </div>
            </article>
          ))}
        </div>
        <div className="flex flex-wrap justify-center gap-3 text-sm text-zinc-400">
          <button
            type="button"
            onClick={onOpenAnalysis}
            className="underline-offset-2 hover:text-white hover:underline"
          >
            {t(`${ns}.available.analysis`, { defaultValue: "Website Analysis" })}
          </button>
          <span aria-hidden>·</span>
          <Link href={repairHref} className="underline-offset-2 hover:text-white hover:underline">
            {t(`${ns}.available.repair`, { defaultValue: "Website Repair" })}
          </Link>
        </div>
      </section>

      {/* VIRTUS OFFICE — human explanation */}
      <section id="office" className="scroll-mt-24 space-y-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.officeBlock.title`, { defaultValue: "Virtus Office" })}
          </h2>
          <p className="mt-3 text-base text-zinc-300 sm:text-lg">
            {t(`${ns}.officeBlock.lead`, {
              defaultValue:
                "Upload a document — Virtus understands it and proposes what can be done.",
            })}
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <OfficeDocsMock />
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">
              {t(`${ns}.officeBlock.canTitle`, {
                defaultValue: "What Virtus can do with a document",
              })}
            </h3>
            <ul className="space-y-2.5 text-sm text-zinc-300">
              {officeCapabilities.map(([key, icon, fallback]) => (
                <li key={key} className="flex gap-2.5">
                  <span aria-hidden>{icon}</span>
                  <span>
                    {t(`${ns}.officeBlock.${key}`, { defaultValue: fallback })}
                  </span>
                </li>
              ))}
            </ul>
            <p className="text-xs leading-relaxed text-amber-100/80">
              {t(`${ns}.officeBlock.legalNote`, {
                defaultValue:
                  "Virtus is not a lawyer and does not replace qualified legal advice. Regulated advice may need a specialist review.",
              })}
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-sky-400/25 bg-sky-500/[0.06] p-5 sm:p-7">
          <h3 className="text-xl font-semibold text-white">
            {t(`${ns}.officeBlock.smartTitle`, {
              defaultValue: "Not sure what to do with a document?",
            })}
          </h3>
          <p className="mt-2 text-sm text-zinc-300">
            {t(`${ns}.officeBlock.smartLead`, {
              defaultValue: "Just upload it.",
            })}
          </p>
          <ol className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {smartSteps.map((key, i) => (
              <li
                key={key}
                className="rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-xs text-zinc-200"
              >
                <span className="font-bold text-sky-300">{i + 1}.</span>{" "}
                {t(`${ns}.officeBlock.${key}`, {
                  defaultValue: [
                    "Recognizes the file",
                    "Understands the content",
                    "Explains it to you",
                    "Proposes actions",
                    "Asks if something is missing",
                    "Runs the chosen task",
                    "Checks the result",
                    "Returns the finished file",
                  ][i],
                })}
              </li>
            ))}
          </ol>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/office/smart"
              className="inline-flex min-h-[44px] items-center justify-center rounded-xl bg-sky-600 px-5 text-sm font-semibold text-white hover:bg-sky-500"
            >
              {t(`${ns}.officeBlock.smartCta`, {
                defaultValue: "Upload to Smart Office →",
              })}
            </Link>
            <Link
              href="/office"
              className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/20 px-5 text-sm font-semibold text-white hover:bg-white/[0.04]"
            >
              {t(`${ns}.officeBlock.openCta`, {
                defaultValue: "Open Virtus Office",
              })}
            </Link>
          </div>
          <p className="mt-4 text-xs leading-relaxed text-zinc-400">
            {t(`${ns}.officeBlock.privacy`, {
              defaultValue:
                "Documents may contain personal data. Access is owner-bound; only necessary data is used. See privacy policy for retention and processing — no absolute “never leaves our servers” claim.",
            })}
          </p>
          <p className="mt-2 text-xs text-zinc-500">
            {t(`${ns}.officeBlock.langNote`, {
              defaultValue:
                "UI language, document language and translation target stay independent.",
            })}
          </p>
        </div>
      </section>

      {/* SELECTED WORK */}
      <section id="work" className="scroll-mt-24 space-y-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.work.title`, { defaultValue: "Selected work" })}
          </h2>
          <p className="mt-2 text-sm text-zinc-400">
            {t(`${ns}.work.demoNote`, {
              defaultValue: "Demo / Showcase — not customer projects",
            })}
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <div className="mb-3 flex items-end justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">
                {t(`${ns}.work.websites`, { defaultValue: "Websites" })}
              </h3>
              <Link href="/site/websites" className="text-sm text-violet-300 hover:underline">
                {t(`${ns}.work.more`, { defaultValue: "More →" })}
              </Link>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {siteWork.map((item) => (
                <a
                  key={item.id}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] transition hover:border-sky-400/40"
                >
                  <div className="aspect-[16/10] bg-zinc-900">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={item.thumb}
                      alt=""
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <p className="p-2.5 text-sm font-medium text-white">{item.title}</p>
                </a>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-end justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">
                {t(`${ns}.work.shops`, { defaultValue: "Online Shops" })}
              </h3>
              <Link href="/site/shops" className="text-sm text-violet-300 hover:underline">
                {t(`${ns}.work.more`, { defaultValue: "More →" })}
              </Link>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {shopWork.map((item) => (
                <a
                  key={item.id}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] transition hover:border-violet-400/40"
                >
                  <div className="aspect-[16/10] bg-zinc-900">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={item.thumb}
                      alt=""
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <p className="p-2.5 text-sm font-medium text-white">{item.title}</p>
                </a>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-end justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">
                {t(`${ns}.work.bots`, { defaultValue: "AI Bots" })}
              </h3>
              <Link href="/site/bots" className="text-sm text-violet-300 hover:underline">
                {t(`${ns}.work.more`, { defaultValue: "More →" })}
              </Link>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {(["receptionist", "support", "sales"] as const).map((v) => (
                <div
                  key={v}
                  className="overflow-hidden rounded-xl border border-emerald-400/20 bg-white/[0.02] p-2"
                >
                  <BotChatMock variant={v} compact />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FOR BUSINESS */}
      <section id="b2b" className="scroll-mt-24 space-y-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t(`${ns}.b2b.title`, { defaultValue: "For business" })}
          </h2>
          <p className="mt-3 text-sm text-zinc-400 sm:text-base">
            {t(`${ns}.b2b.sub`, {
              defaultValue: "AI Receptionist, automation and AI employees you can order today.",
            })}
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {b2b.map((offer) => (
            <article
              key={offer.id}
              className={`flex flex-col rounded-2xl border p-5 sm:p-6 ${
                offer.featured
                  ? "border-emerald-400/40 bg-emerald-500/[0.07]"
                  : "border-white/10 bg-white/[0.03]"
              }`}
            >
              <h3 className="text-xl font-semibold text-white">{offer.title}</h3>
              <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                {t(`${ns}.b2b.forLabel`, { defaultValue: "For whom" })}
              </p>
              <p className="mt-1 text-sm text-zinc-300">{offer.forWhom}</p>
              <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                {t(`${ns}.b2b.doesLabel`, { defaultValue: "What it does" })}
              </p>
              <p className="mt-1 flex-1 text-sm text-zinc-300">{offer.does}</p>
              <p className="mt-4 text-lg font-semibold text-white">{offer.price}</p>
              <Link
                href={offer.href}
                onClick={() => logCommerceEvent("tier_select", offer.id, "site")}
                className={`mt-5 inline-flex min-h-[44px] items-center justify-center rounded-xl px-4 text-sm font-semibold text-white ${
                  offer.featured
                    ? "bg-emerald-600 hover:bg-emerald-500"
                    : "bg-violet-600 hover:bg-violet-500"
                }`}
              >
                {offer.cta}
              </Link>
            </article>
          ))}
        </div>
      </section>

      {/* WHY */}
      <section id="warum" className="scroll-mt-24 mx-auto max-w-3xl space-y-6">
        <h2 className="text-center text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          {t(`${ns}.why.title`, { defaultValue: "Why Virtus Core" })}
        </h2>
        <p className="text-center text-sm text-zinc-400 sm:text-base">
          {t(`${ns}.why.sub`, {
            defaultValue:
              "A digital company instead of an agency queue — you order, receive and control.",
          })}
        </p>
        <ul className="space-y-4">
          {(
            [
              ["p1t", "p1d", "Clear prices", "Website, shop and AI — without hidden agency hours."],
              ["p2t", "p2d", "Fast delivery", "You review and publish after the build."],
              [
                "p3t",
                "p3d",
                "Your panel",
                "From Business: Client Workspace — edit content and media yourself.",
              ],
            ] as const
          ).map(([tk, dk, tf, df]) => (
            <li key={tk} className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-4">
              <p className="font-semibold text-white">
                {t(`${ns}.why.${tk}`, { defaultValue: tf })}
              </p>
              <p className="mt-1 text-sm text-zinc-400">
                {t(`${ns}.why.${dk}`, { defaultValue: df })}
              </p>
            </li>
          ))}
        </ul>
        <p className="text-center">
          <Link href="/why" className="text-sm font-semibold text-violet-300 hover:underline">
            {t(`${ns}.why.link`, { defaultValue: "Compare with agencies →" })}
          </Link>
        </p>
      </section>

      {/* FINAL CTA */}
      <section
        id="starten"
        className="scroll-mt-24 rounded-2xl border border-violet-400/25 bg-gradient-to-br from-violet-600/20 to-transparent px-6 py-10 text-center sm:px-10"
      >
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          {t(`${ns}.final.title`, { defaultValue: "Ready to start?" })}
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-zinc-300">
          {t(`${ns}.final.sub`, {
            defaultValue:
              "Choose a website, shop, AI bot or Virtus Office — clear path to order.",
          })}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href={websiteOrderHref}
            className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-violet-600 px-6 text-sm font-semibold text-white hover:bg-violet-500"
          >
            {t(`${ns}.final.cta`, { defaultValue: "Start a project" })}
          </Link>
          <Link
            href="/office"
            className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/20 px-6 text-sm font-semibold text-white hover:bg-white/[0.04]"
          >
            {t(`${ns}.final.office`, { defaultValue: "Open Virtus Office" })}
          </Link>
          <Link
            href="/kontakt"
            className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/20 px-6 text-sm font-semibold text-white hover:bg-white/[0.04]"
          >
            {t(`${ns}.final.consult`, { defaultValue: "Request a consultation" })}
          </Link>
        </div>
      </section>

      <nav
        className="flex flex-wrap justify-center gap-4 border-t border-white/10 pt-8 text-xs text-zinc-500"
        aria-label={t(`${ns}.legal.nav`, { defaultValue: "Legal" })}
      >
        <Link href="/impressum" className="hover:text-zinc-300">
          {t(`${ns}.legal.impressum`, { defaultValue: "Impressum" })}
        </Link>
        <Link href="/datenschutz" className="hover:text-zinc-300">
          {t(`${ns}.legal.privacy`, { defaultValue: "Privacy" })}
        </Link>
        <Link href="/ai-disclaimer" className="hover:text-zinc-300">
          {t(`${ns}.hero.kiLink`, { defaultValue: "AI notice" })}
        </Link>
      </nav>
    </div>
  );
}
