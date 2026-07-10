import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${ASSISTANT_NAME} — цифровая компания`,
  `${ASSISTANT_NAME} от ${BRAND_NAME}: проекты, документы, сайты. Лендинг под ключ — от 350 €.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
