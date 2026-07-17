import type { Metadata } from "next";
import { KontaktClient } from "./KontaktClient";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Kontakt",
  "Virtus Core Support: E-Mail und Bestellung. Antworten auf Deutsch.",
  "/kontakt"
);

export default function KontaktPage() {
  return <KontaktClient />;
}
