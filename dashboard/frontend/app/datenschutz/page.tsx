import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { LegalPageLayout } from "../components/LegalPageLayout";
import { Card } from "../components/ui";
import { CONTACT_EMAIL, LEGAL } from "../lib/siteConfig";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Datenschutz",
  "Datenschutzerklärung gemäß DSGVO für Virtus Core.",
  "/datenschutz"
);

function field(value: string, fallback: string) {
  return value.trim() || fallback;
}

export default function DatenschutzPage() {
  const name = field(LEGAL.fullName, "[Name]");
  const address = field(LEGAL.address, "[Adresse]");
  const phone = field(LEGAL.phone, "[Telefon]");

  return (
    <PublicPageShell>
      <LegalPageLayout title="Datenschutzerklärung" subtitle="Stand: Juli 2026">
        <Card hover={false} padding="md" className="mt-4 space-y-4 text-sm leading-relaxed text-genesis-muted">
          <div>
            <h2 className="text-lg font-semibold text-white">1. Verantwortlicher</h2>
            <p className="mt-2">
              {name} — Virtus Core
              <br />
              {address}
              <br />
              E-Mail: {CONTACT_EMAIL}
              <br />
              Telefon: {phone}
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">2. Verarbeitungen</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Website-Betrieb: Server-Logfiles (IP, Browser, Zeitstempel)</li>
              <li>Bestellung: Name, Kontaktdaten, Bestelldaten</li>
              <li>Zahlung: Zahlungsdaten über Stripe</li>
              <li>E-Mail: Transaktionsbestätigungen</li>
            </ul>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">3. Dienstleister</h2>
            <p className="mt-2">
              Vercel, Railway, Resend, Stripe — AVV vor Live-Bestellungen.
            </p>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">4. Ihre Rechte</h2>
            <p className="mt-2">
              Auskunft, Berichtigung, Löschung — {CONTACT_EMAIL}.
            </p>
          </div>
        </Card>
      </LegalPageLayout>
    </PublicPageShell>
  );
}
