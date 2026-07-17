import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Landing Page Neustart · ${BRAND_NAME}`,
  `Moderne Landing Page in 5–7 Werktagen. Pakete 350 / 650 / 1.200 €. Kein WordPress-Flickwerk — digitaler Neustart.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
