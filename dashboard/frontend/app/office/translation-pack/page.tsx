import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicPageMetadata } from "../../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  `Translation Pack · Virtus Office · ${BRAND_NAME}`,
  "Dokumente als Übersetzungspaket mit strukturierter Ausgabe und Qualitätsprüfung.",
  "/office/translation-pack",
);

export default function OfficeTranslationPackRoute() {
  return <OfficeServiceFlow kind="translation_pack" />;
}
