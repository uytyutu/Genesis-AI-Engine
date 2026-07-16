import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Landing Page Neustart · ${BRAND_NAME}`,
  `Современная Landing Page за 5–7 дней. Пакеты 350 / 650 / 1 200 €. Не починка WordPress — digitaler Neustart.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
