import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Übersetzung · Virtus Office · ${BRAND_NAME}`,
  "Dokument übersetzen: PDF, Word, Foto oder Scan. Zielsprache wählen — noch keine Zahlung.",
  "/office/translate",
);

export default function VirtusOfficeTranslatePage() {
  return <OfficeServiceFlow kind="translate" />;
}
