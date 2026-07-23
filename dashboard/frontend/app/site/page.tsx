import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Digital ecosystem for business · ${BRAND_NAME}`,
  `Websites (Basic 350 € · Business 650 € · Premium 1200 €), AI assistants, automation. Clear packages — order without chat. Vector helps if you need advice.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
