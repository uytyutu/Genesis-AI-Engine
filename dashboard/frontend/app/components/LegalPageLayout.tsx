import type { ReactNode } from "react";
import { PublicPageHero } from "./PublicPageHero";
import { LegalProse } from "./LegalProse";
import { LEGAL_PENDING } from "../lib/siteConfig";

export function LegalPageLayout({
  title,
  subtitle,
  children,
  pending,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  /** When set, overrides env-based LEGAL_PENDING for API-generated docs */
  pending?: boolean;
}) {
  const showPending = pending ?? LEGAL_PENDING;
  return (
    <>
      <PublicPageHero title={title} description={subtitle} centered />
      <LegalProse showPendingBanner={showPending}>{children}</LegalProse>
    </>
  );
}
