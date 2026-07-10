import type { Metadata } from "next";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${ASSISTANT_NAME} — ИИ-помощник`,
  `ИИ-помощник ${ASSISTANT_NAME} от ${BRAND_NAME}: объяснит продукт, подберёт решение, покажет цену. Лендинг под ключ — от 350 €.`,
  "/site"
);

export default function Page() {
  return <SitePage />;
}
