import type { Metadata } from "next";
import { LegalDocView } from "@/components/LegalDocView";
import { getLegalDocument } from "@/lib/legal/documents";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Impressum und Anbieterkennzeichnung gemäß § 5 DDG.",
  robots: { index: true, follow: true },
};

export default async function ImpressumPage() {
  const doc = await getLegalDocument("impressum");
  return <LegalDocView doc={doc} />;
}
