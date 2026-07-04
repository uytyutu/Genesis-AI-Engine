import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { LegalProse } from "../components/LegalProse";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "AGB",
  "Allgemeine Geschäftsbedingungen für Website-Dienstleistungen von Genesis.",
  "/agb"
);

export default function AgbPage() {
  return (
    <PublicPageShell>
      <LegalProse>
        <h1 className="text-3xl font-bold">Allgemeine Geschäftsbedingungen (AGB)</h1>
        <p className="mt-2 text-sm text-genesis-muted">Stand: Juli 2026</p>

        <section className="mt-8 space-y-6 text-sm leading-relaxed text-genesis-muted">
          <div>
            <h2 className="text-lg font-semibold text-white">§ 1 Geltungsbereich</h2>
            <p className="mt-2">
              Diese AGB gelten für Verträge über die Erstellung von Websites und zugehörige
              Dienstleistungen zwischen Genesis AI Engine und dem Kunden.
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">§ 2 Leistungen und Pakete</h2>
            <p className="mt-2">
              Umfang und Preis ergeben sich aus dem gewählten Paket zum Zeitpunkt der Bestellung
              (siehe{" "}
              <Link href="/order" className="text-genesis-accent hover:underline">
                Bestellseite
              </Link>
              ). Änderungswünsche außerhalb des Pakets werden gesondert vereinbart.
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">§ 3 Vertragsschluss</h2>
            <p className="mt-2">
              Der Vertrag kommt mit erfolgreicher Online-Zahlung zustande. Vorherige Anfragen sind
              unverbindlich.
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">§ 4 Widerrufsrecht</h2>
            <p className="mt-2">
              Verbrauchern steht ein gesetzliches Widerrufsrecht zu. Bei digitalen Dienstleistungen
              kann das Widerrufsrecht erlöschen, wenn die Ausführung mit ausdrücklicher Zustimmung
              vor Ablauf der Widerrufsfrist begonnen wurde.
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">§ 5 Haftung</h2>
            <p className="mt-2">
              Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit. Im Übrigen gilt die
              gesetzliche Haftungsbeschränkung.
            </p>
          </div>
        </section>
      </LegalProse>
    </PublicPageShell>
  );
}
