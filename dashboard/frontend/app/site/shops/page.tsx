"use client";

import { useTranslation } from "react-i18next";
import { SiteAtmospherePage } from "../../components/storefront/SiteAtmospherePage";
import { shopShowcaseSlides } from "../../lib/vitrineShowcaseCatalog";

export default function SiteShopsPage() {
  const { t } = useTranslation("site");
  const examples = shopShowcaseSlides()
    .filter((s, i, arr) => arr.findIndex((x) => x.href === s.href) === i)
    .slice(0, 10)
    .map((s) => ({
      title: s.title,
      blurb: s.blurb,
      thumb: s.thumb,
      href: s.href,
      visual: "photo" as const,
    }));

  return (
    <SiteAtmospherePage
      kind="shops"
      title={t("agencyHub.atmosphere.shopsTitle", {
        defaultValue: "Online shops built to sell",
      })}
      subtitle={t("agencyHub.atmosphere.shopsSub", {
        defaultValue:
          "Product catalog, cart and owner admin — Stripe and shipping connected by you.",
      })}
      ctaLabel={t("agencyHub.atmosphere.shopsCta", {
        defaultValue: "Order an online shop →",
      })}
      ctaHref="/order/shop"
      secondaryLabel={t("agencyHub.atmosphere.seePackages", {
        defaultValue: "See packages on Virtus Core",
      })}
      secondaryHref="/site"
      examples={examples}
    />
  );
}
