import type { Metadata } from "next";
import { LegalDocView } from "@/components/LegalDocView";
import { getLegalDocument } from "@/lib/legal/documents";

export const metadata: Metadata = {
  title: "AGB",
  description: "Allgemeine Geschäftsbedingungen für ANON.",
};

export default async function AgbPage() {
  const doc = await getLegalDocument("agb");
  return <LegalDocView doc={doc} />;
}
