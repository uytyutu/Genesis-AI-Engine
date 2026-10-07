import type { Metadata } from "next";
import { LegalDocView } from "@/components/LegalDocView";
import { getLegalDocument } from "@/lib/legal/documents";

export const metadata: Metadata = {
  title: "Datenschutz",
  description: "Datenschutzerklärung für ANON.",
};

export default async function DatenschutzPage() {
  const doc = await getLegalDocument("datenschutz");
  return <LegalDocView doc={doc} />;
}
