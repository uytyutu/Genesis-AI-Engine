import type { ReactNode } from "react";
import { PublicPageHero } from "./PublicPageHero";
import { LegalProse } from "./LegalProse";

export function LegalPageLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <>
      <PublicPageHero title={title} description={subtitle} centered />
      <LegalProse>{children}</LegalProse>
    </>
  );
}
