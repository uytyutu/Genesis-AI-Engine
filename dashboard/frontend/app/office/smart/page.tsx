import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Smart Office · Virtus Office · ${BRAND_NAME}`,
  "Datei hochladen — Virtus schlägt die passende Aufgabe vor.",
  "/office/smart",
);

export default function OfficeSmartPage() {
  return <OfficeServiceFlow kind="smart" />;
}
