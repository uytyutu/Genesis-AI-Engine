import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${ASSISTANT_NAME} — ваш цифровой сотрудник`,
  `${ASSISTANT_NAME} от ${BRAND_NAME}: расскажите о бизнесе — черновик сайта появится сразу. Оформите права на тот же результат.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
