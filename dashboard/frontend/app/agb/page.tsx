import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { LegalPageLayout } from "../components/LegalPageLayout";
import { Card } from "../components/ui";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  "AGB",
  `Allgemeine Geschäftsbedingungen für Website-Dienstleistungen von ${BRAND_NAME}.`,
  "/agb"
);

const SECTIONS = [
  {
    title: "§ 1 Geltungsbereich",
    body: "Diese AGB gelten für Verträge über die Erstellung von Websites und zugehörige Dienstleistungen zwischen Virtus Core und dem Kunden.",
  },
  {
    title: "§ 2 Leistungen und Pakete",
    body: "Umfang und Preis ergeben sich aus dem gewählten Paket zum Zeitpunkt der Bestellung.",
    link: { href: "/order", label: "Bestellseite" },
  },
  {
    title: "§ 3 Vertragsschluss",
    body: "Der Vertrag kommt mit erfolgreicher Online-Zahlung zustande. Vorherige Anfragen sind unverbindlich.",
  },
  {
    title: "§ 4 Widerrufsrecht",
    body: "Verbrauchern steht ein gesetzliches Widerrufsrecht zu. Bei digitalen Dienstleistungen kann es erlöschen, wenn die Ausführung mit Zustimmung vor Fristende beginnt.",
  },
  {
    title: "§ 5 Haftung",
    body: "Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit. Im Übrigen gilt die gesetzliche Haftungsbeschränkung.",
  },
];

export default function AgbPage() {
  return (
    <PublicPageShell>
      <LegalPageLayout
        title="Allgemeine Geschäftsbedingungen (AGB)"
        subtitle="Stand: Juli 2026"
      >
        <div className="mt-4 space-y-4">
          {SECTIONS.map((s) => (
            <Card key={s.title} hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">{s.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-genesis-muted">
                {s.body}
                {"link" in s && s.link && (
                  <>
                    {" "}
                    (siehe{" "}
                    <Link href={s.link.href} className="text-genesis-accent hover:underline">
                      {s.link.label}
                    </Link>
                    ).
                  </>
                )}
              </p>
            </Card>
          ))}
        </div>
      </LegalPageLayout>
    </PublicPageShell>
  );
}
