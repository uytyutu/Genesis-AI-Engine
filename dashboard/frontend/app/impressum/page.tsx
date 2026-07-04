import type { Metadata } from "next";
import { PublicPageShell } from "../components/PublicPageShell";
import { LegalProse } from "../components/LegalProse";
import { CONTACT_EMAIL, LEGAL } from "../lib/siteConfig";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Impressum",
  "Impressum und Anbieterkennzeichnung gemäß § 5 DDG.",
  "/impressum"
);

function field(value: string, fallback: string) {
  return value.trim() || fallback;
}

export default function ImpressumPage() {
  const name = field(LEGAL.fullName, "[Name nach Gewerbeanmeldung]");
  const address = field(LEGAL.address, "[Adresse nach Gewerbeanmeldung]");
  const phone = field(LEGAL.phone, "[Telefon]");

  return (
    <PublicPageShell>
      <LegalProse>
        <h1 className="text-3xl font-bold">Impressum</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz)
        </p>

        <section className="mt-8 space-y-2 text-sm leading-relaxed">
          <p>
            {name}
            <br />
            Genesis AI Engine
            <br />
            {address}
          </p>
          <p className="mt-4">
            <strong>Kontakt</strong>
            <br />
            Telefon: {phone}
            <br />
            E-Mail:{" "}
            <a href={`mailto:${CONTACT_EMAIL}`} className="text-genesis-accent hover:underline">
              {CONTACT_EMAIL}
            </a>
            <br />
            Website: genesis-ai-engine.com
          </p>
          {LEGAL.vatId && (
            <p className="mt-4">
              Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: {LEGAL.vatId}
            </p>
          )}
        </section>

        <section className="mt-10 space-y-3 text-sm text-genesis-muted">
          <h2 className="text-lg font-semibold text-white">EU-Streitschlichtung</h2>
          <p>
            Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{" "}
            <a
              href="https://ec.europa.eu/consumers/odr/"
              className="text-genesis-accent hover:underline"
              rel="noopener noreferrer"
              target="_blank"
            >
              ec.europa.eu/consumers/odr
            </a>
          </p>
          <h2 className="pt-4 text-lg font-semibold text-white">
            Verbraucherstreitbeilegung
          </h2>
          <p>
            Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
            Verbraucherschlichtungsstelle teilzunehmen.
          </p>
        </section>
      </LegalProse>
    </PublicPageShell>
  );
}
