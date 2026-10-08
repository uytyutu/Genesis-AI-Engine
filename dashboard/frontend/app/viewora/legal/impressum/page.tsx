import type { Metadata } from "next";
import { CONTACT_EMAIL, LEGAL } from "../../../lib/siteConfig";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Impressum Virtus Video AI — Angaben gemäß § 5 DDG",
  robots: { index: true, follow: true },
};

export default function VieworaImpressumPage() {
  return (
    <article className="viewora-legal">
      <h1>Impressum</h1>
      <p>Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz)</p>

      <h2>Diensteanbieter</h2>
      <p>
        {LEGAL.fullName}
        <br />
        {LEGAL.address}
        {LEGAL.phone ? (
          <>
            <br />
            Tel: {LEGAL.phone}
          </>
        ) : null}
        <br />
        E-Mail: {CONTACT_EMAIL}
      </p>

      <h2>Produkt</h2>
      <p>
        <strong>Virtus Video AI</strong> ist ein professionelles AI Content Studio der Marke Virtus
        Core. Es handelt sich um einen hochprofessionellen KI-gestützten Generator für
        Kurzvideo- und Content-Pakete (Hooks, Skripte, Captions, Storyboards, Scores) für
        Creator und Unternehmen.
      </p>

      <h2>Verantwortlich für den Inhalt</h2>
      <p>
        {LEGAL.fullName}, {LEGAL.address}
      </p>

      {LEGAL.vatId ? (
        <>
          <h2>Umsatzsteuer-ID</h2>
          <p>{LEGAL.vatId}</p>
        </>
      ) : null}

      <h2>Streitschlichtung</h2>
      <p>
        Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS)
        bereit:{" "}
        <a href="https://ec.europa.eu/consumers/odr/" rel="noopener noreferrer">
          https://ec.europa.eu/consumers/odr/
        </a>
        . Wir sind nicht verpflichtet und nicht bereit, an Streitbeilegungsverfahren vor
        einer Verbraucherschlichtungsstelle teilzunehmen.
      </p>
    </article>
  );
}
