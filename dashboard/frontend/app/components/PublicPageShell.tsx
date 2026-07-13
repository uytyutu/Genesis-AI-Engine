"use client";

import { Suspense } from "react";
import { usePathname } from "next/navigation";
import { PublicSiteFooter } from "./PublicSiteFooter";
import { PublicSiteHeader } from "./PublicSiteHeader";
import { useTranslation } from "react-i18next";
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
  return (
    <div
      className={
        hideChrome
          ? "h-[100dvh] overflow-hidden bg-genesis-bg"
          : "mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 sm:py-8"
      }
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-genesis-accent focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
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
  );
}
