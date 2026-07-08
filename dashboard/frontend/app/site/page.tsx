import type { Metadata } from "next";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${ASSISTANT_NAME} — расскажите, что хотите создать`,
  `ИИ-помощник ${ASSISTANT_NAME} от ${BRAND_NAME}: объяснит продукт, подберёт решение, покажет цену. Сайты для бизнеса — от 48 часов.`,
  "/site"
);

export default function Page() {
  return <SitePage />;
}
