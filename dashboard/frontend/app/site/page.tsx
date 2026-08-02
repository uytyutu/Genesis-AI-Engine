import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `App Store for business · ${BRAND_NAME}`,
  `Connect modules — websites, AI chatbots, automation. Try Vector free. Packages from 350 €. AI-assisted delivery with edit requests after purchase.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
