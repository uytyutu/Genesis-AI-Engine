"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { useTranslation } from "react-i18next";
import { BRAND_NAME } from "../../lib/publicBrand";
import {
  SHOWCASE_PANES,
  shopShowcaseSlides,
  websiteShowcaseSlides,
  type ShowcasePaneId,
} from "../../lib/vitrineShowcaseCatalog";
import {
  AutomationFlowMock,
  BotChatMock,
  OfficeDocsMock,
  ShopStorefrontMock,
  WebsiteBrowserMock,
} from "./VitrineProductMocks";

const PANE_ORDER: ShowcasePaneId[] = [
  "websites",
  "shops",
  "bots",
  "office",
  "automation",
];

type Props = {
  marketSelect?: ReactNode;
};

export function VirtusCommercialShowcase({ marketSelect }: Props) {
  const { t } = useTranslation("site");
  const [active, setActive] = useState<ShowcasePaneId>("websites");
  const [siteIdx, setSiteIdx] = useState(0);
  const [shopIdx, setShopIdx] = useState(0);
  const paused = useRef(false);
  const dragX = useRef<number | null>(null);

  const sites = websiteShowcaseSlides();
  const shops = shopShowcaseSlides();
  const site = sites[siteIdx % Math.max(sites.length, 1)];
  const shop = shops[shopIdx % Math.max(shops.length, 1)];

  const go = useCallback((id: ShowcasePaneId) => {
    setActive(id);
    if (id === "websites" && sites.length) {
      setSiteIdx((i) => (i + 1) % sites.length);
    }
    if (id === "shops" && shops.length) {
      setShopIdx((i) => (i + 1) % shops.length);
    }
  }, [shops.length, sites.length]);

  useEffect(() => {
    const id = window.setInterval(() => {
      if (paused.current) return;
      setActive((prev) => {
        const idx = PANE_ORDER.indexOf(prev);
        const next = PANE_ORDER[(idx + 1) % PANE_ORDER.length];
        if (next === "websites" && sites.length) {
          setSiteIdx((i) => (i + 1) % sites.length);
        }
        if (next === "shops" && shops.length) {
          setShopIdx((i) => (i + 1) % shops.length);
        }
        return next;
      });
    }, 5200);
    return () => window.clearInterval(id);
  }, [shops.length, sites.length]);

  function onPointerDown(e: ReactPointerEvent) {
    dragX.current = e.clientX;
  }
  function onPointerUp(e: ReactPointerEvent) {
    if (dragX.current == null) return;
    const dx = e.clientX - dragX.current;
    dragX.current = null;
    if (Math.abs(dx) < 48) return;
    const idx = PANE_ORDER.indexOf(active);
    const next =
      dx < 0
        ? PANE_ORDER[(idx + 1) % PANE_ORDER.length]
        : PANE_ORDER[(idx - 1 + PANE_ORDER.length) % PANE_ORDER.length];
    go(next);
  }

  const paneMeta = SHOWCASE_PANES.find((p) => p.id === active)!;
  const titleKey = `agencyHub.showcase.panes.${active}.title`;
  const blurbKey = `agencyHub.showcase.panes.${active}.blurb`;
  const titleFallbacks: Record<ShowcasePaneId, string> = {
    websites: "Create websites",
    shops: "Build online shops",
    bots: "AI bots",
    office: "Virtus Office",
    automation: "Automate",
  };
  const blurbFallbacks: Record<ShowcasePaneId, string> = {
    websites: "Professional sites for businesses and services — real demo examples.",
    shops: "Catalog, product cards, cart and shop admin — built to sell.",
    bots: "Receptionist, support and sales — chat UI, not a website screenshot.",
    office: "PDF · DOCX · Excel · OCR · translate · calculate — upload and work.",
    automation: "Inquiry → qualify → task → follow-up for your business process.",
  };

  return (
    <section
      className="vc-showcase relative"
      onMouseEnter={() => {
        paused.current = true;
      }}
      onMouseLeave={() => {
        paused.current = false;
      }}
    >
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-semibold tracking-[0.28em] text-white/70">
          {BRAND_NAME.toUpperCase()}
        </p>
        <h1 className="mt-4 text-[2.2rem] font-semibold leading-[1.05] tracking-[-0.035em] text-white sm:text-5xl lg:text-[3.25rem]">
          {t("agencyHub.showcase.headline", {
            defaultValue: "Digital products. AI services. Real work.",
          })}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-zinc-300 sm:text-base">
          {t("agencyHub.showcase.subline", {
            defaultValue:
              "We create websites, online shops, AI bots and Virtus Office — from a finished digital product to documents and business tasks.",
          })}
        </p>
        {marketSelect ? (
          <div className="mx-auto mt-5 flex max-w-sm justify-center">{marketSelect}</div>
        ) : null}
      </div>

      {/* Direction tabs */}
      <div
        className="mt-8 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        role="tablist"
        aria-label={t("agencyHub.showcase.tabsLabel", {
          defaultValue: "Virtus Core products",
        })}
      >
        {SHOWCASE_PANES.map((p) => {
          const selected = active === p.id;
          return (
            <button
              key={p.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => go(p.id)}
              className={`shrink-0 rounded-full px-3.5 py-2 text-xs font-semibold transition sm:text-sm ${
                selected
                  ? "bg-white text-zinc-950"
                  : "border border-white/15 bg-white/[0.04] text-zinc-300 hover:border-white/30 hover:bg-white/[0.07]"
              }`}
            >
              {t(`agencyHub.showcase.tabs.${p.id}`, {
                defaultValue: titleFallbacks[p.id],
              })}
            </button>
          );
        })}
      </div>

      {/* Interactive stage */}
      <div
        className="vc-showcase__stage relative mt-5 touch-pan-y"
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        role="tabpanel"
      >
        <div className="grid items-stretch gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.15fr)] lg:gap-8">
          <div className="flex flex-col justify-center space-y-4 text-left">
            <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              {t(titleKey, { defaultValue: titleFallbacks[active] })}
            </h2>
            <p className="max-w-md text-sm leading-relaxed text-zinc-300 sm:text-base">
              {t(blurbKey, { defaultValue: blurbFallbacks[active] })}
            </p>
            <div className="flex flex-wrap gap-3 pt-1">
              <Link
                href={paneMeta.ctaHref}
                className="inline-flex min-h-[44px] items-center justify-center rounded-xl bg-violet-600 px-5 text-sm font-semibold text-white hover:bg-violet-500"
              >
                {t(`agencyHub.showcase.cta.${active}`, {
                  defaultValue: "Open →",
                })}
              </Link>
              {paneMeta.href !== paneMeta.ctaHref ? (
                <Link
                  href={paneMeta.href}
                  className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/20 px-5 text-sm font-semibold text-white hover:bg-white/[0.04]"
                >
                  {t("agencyHub.showcase.seeMore", {
                    defaultValue: "See examples →",
                  })}
                </Link>
              ) : null}
            </div>
            <p className="text-[11px] text-zinc-500">
              {t("agencyHub.showcase.dragHint", {
                defaultValue: "Swipe or use tabs — each product has its own visual.",
              })}
            </p>
          </div>

          <div className="vc-showcase__frame relative min-h-[280px] sm:min-h-[320px]">
            {active === "websites" && site?.thumb ? (
              <WebsiteBrowserMock thumb={site.thumb} title={site.title} />
            ) : null}
            {active === "shops" && shop?.thumb ? (
              <ShopStorefrontMock thumb={shop.thumb} title={shop.title} />
            ) : null}
            {active === "bots" ? <BotChatMock variant="receptionist" /> : null}
            {active === "office" ? <OfficeDocsMock /> : null}
            {active === "automation" ? <AutomationFlowMock /> : null}
          </div>
        </div>

        {/* Progress dots */}
        <div className="mt-4 flex justify-center gap-1.5" aria-hidden>
          {PANE_ORDER.map((id) => (
            <button
              key={id}
              type="button"
              className={`h-1.5 rounded-full transition-all ${
                id === active ? "w-6 bg-white" : "w-1.5 bg-white/30"
              }`}
              onClick={() => go(id)}
              aria-label={id}
            />
          ))}
        </div>
      </div>

      <p className="mt-4 text-center text-[11px] text-zinc-500">
        {t("agencyHub.hero.ki", {
          defaultValue:
            "AI-assisted delivery. You can request changes after purchase where the product allows.",
        })}{" "}
        <Link href="/ai-disclaimer" className="text-violet-300 hover:underline">
          {t("agencyHub.hero.kiLink", { defaultValue: "AI notice" })}
        </Link>
      </p>
    </section>
  );
}
