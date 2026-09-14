"use client";

import { useTranslation } from "react-i18next";
import { SiteAtmospherePage } from "../../components/storefront/SiteAtmospherePage";
import { websiteShowcaseSlides } from "../../lib/vitrineShowcaseCatalog";

export default function SiteWebsitesPage() {
  const { t } = useTranslation("site");
  const examples = websiteShowcaseSlides()
    .slice(0, 12)
    .map((s) => ({
      title: s.title,
      blurb: s.blurb,
      thumb: s.thumb,
      href: s.href,
      visual: "photo" as const,
    }));

  return (
    <SiteAtmospherePage
      kind="websites"
      title={t("agencyHub.atmosphere.websitesTitle", {
        defaultValue: "Websites for real businesses",
      })}
      subtitle={t("agencyHub.atmosphere.websitesSub", {
        defaultValue:
          "Industry-ready sites with contact, legal pages and a clear path to order.",
      })}
      ctaLabel={t("agencyHub.atmosphere.websitesCta", {
        defaultValue: "Order a website →",
      })}
      ctaHref="/order?form=1"
      secondaryLabel={t("agencyHub.atmosphere.seePackages", {
        defaultValue: "See packages on Virtus Core",
      })}
      secondaryHref="/site#b2b"
      examples={examples}
    />
  );
}
