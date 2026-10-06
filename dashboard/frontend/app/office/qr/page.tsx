import type { Metadata } from "next";
import { OfficeQrPage } from "../../components/office/OfficeQrPage";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicPageMetadata } from "../../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  `QR Code kostenlos · Virtus Office · ${BRAND_NAME}`,
  "QR-Codes für Links, WhatsApp, Karten, E-Mail, WLAN und Kontaktdaten kostenlos erstellen.",
  "/office/qr",
);

export default function OfficeQrRoute() {
  return <OfficeQrPage />;
}
