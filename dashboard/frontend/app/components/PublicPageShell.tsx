"use client";

import { Suspense } from "react";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import { PublicSiteFooter } from "./PublicSiteFooter";
import { PublicSiteHeader } from "./PublicSiteHeader";
import { StorefrontAtmosphere } from "./storefront/StorefrontAtmosphere";
import { isCustomerPurchasePath } from "../lib/surfaceNavConfig";

export function PublicPageShell({
  children,
  hideChrome = false,
  minimal = false,
  customerDecisionFlow,
}: {
  children: React.ReactNode;
  hideChrome?: boolean;
  /** PE-1 — work surface: header only, no footer chrome */
  minimal?: boolean;
  /** Rule A — hide competing public nav on purchase path */
  customerDecisionFlow?: boolean;
}) {
  const { t } = useTranslation("common");
  const pathname = usePathname() ?? "";
  const customerFlow = customerDecisionFlow ?? isCustomerPurchasePath(pathname);
  const sitePath =
    pathname === "/site" || pathname.startsWith("/site/");
  const storefrontLook = (customerFlow || sitePath) && !hideChrome;
  return (
    <div
      data-vie-engine={sitePath ? "visual_intelligence_v1" : undefined}
      data-vie-surface={sitePath ? "platform" : undefined}
      data-vie-niche={sitePath ? "computer" : undefined}
      data-vie-motion={sitePath ? "premium" : undefined}
      className={
        hideChrome
          ? "h-[100dvh] overflow-hidden bg-genesis-bg"
          : storefrontLook
            ? "storefront relative isolate min-h-screen overflow-x-hidden vie-motion-premium"
            : "mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 sm:py-8"
      }
    >
      {storefrontLook ? <StorefrontAtmosphere /> : null}
      <div
        className={
          storefrontLook
            ? "relative z-10 mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 sm:py-8"
            : undefined
        }
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-genesis-accent focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
          suppressHydrationWarning
        >
          {t("skipToContent")}
        </a>
        {!hideChrome && (
          <Suspense fallback={null}>
            <PublicSiteHeader customerDecisionFlow={customerFlow} />
          </Suspense>
        )}
        <div
          id="main-content"
          className={hideChrome ? "h-full" : "animate-fade-up"}
          role="main"
        >
          {children}
        </div>
        {!hideChrome && !minimal && <PublicSiteFooter />}
      </div>
    </div>
  );
}
