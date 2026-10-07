import type { Metadata } from "next";
import { LegalDocView } from "@/components/LegalDocView";
import { getLegalDocument } from "@/lib/legal/documents";

export const metadata: Metadata = {
  title: "Cookies",
  description: "Cookie-Richtlinie für ANON.",
};

export default async function CookiesPage() {
  const doc = await getLegalDocument("cookies");
  return <LegalDocView doc={doc} />;
}
