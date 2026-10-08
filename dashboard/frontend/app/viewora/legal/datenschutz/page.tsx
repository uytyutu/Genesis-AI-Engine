import type { Metadata } from "next";
import { CONTACT_EMAIL, LEGAL } from "../../../lib/siteConfig";

export const metadata: Metadata = {
  title: "Datenschutz",
  description: "Datenschutzerklärung Virtus Video AI (DSGVO)",
  robots: { index: true, follow: true },
};

export default function VieworaPrivacyPage() {
  return (
    <article className="viewora-legal">
      <h1>Datenschutzerklärung</h1>
      <p>für den Dienst Virtus Video AI (AI Content Studio) · Virtus Core</p>

      <h2>1. Verantwortlicher</h2>
      <p>
        {LEGAL.fullName}, {LEGAL.address}, E-Mail: {CONTACT_EMAIL}
      </p>

      <h2>2. Welche Daten wir verarbeiten</h2>
      <ul>
        <li>Account-Kennung (lokal / Server), E-Mail bei Checkout</li>
        <li>Prompts, Briefings, hochgeladene Quellhinweise für Content-Jobs</li>
        <li>Nutzungs- und Abrechnungsdaten (Plan, Credits, Bestellungen)</li>
        <li>Zahlungsdaten über Stripe (wir speichern keine vollständigen Kartendaten)</li>
        <li>Technische Logs zur Stabilität und Missbrauchsprävention</li>
      </ul>

      <h2>3. Zwecke & Rechtsgrundlagen</h2>
      <p>
        Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO), berechtigte Interessen an sicherem
        Betrieb (lit. f), Einwilligung wo erforderlich (lit. a), gesetzliche Pflichten (lit.
        c).
      </p>

      <h2>4. KI-Verarbeitung</h2>
      <p>
        Virtus Video AI nutzt KI-Orchestrierung, um Content-Pakete zu erstellen. Eingaben können an
        ausgewählte Rechenanbieter weitergegeben werden, soweit dies zur Leistung nötig ist.
        Modellnamen werden Kunden nicht als Auswahl angeboten. Details:{" "}
        <a href="/viewora/legal/ki-hinweis">KI-Hinweis</a>.
      </p>

      <h2>5. Speicherdauer</h2>
      <p>
        Contentrelevante Jobs und Abrechnungsdaten speichern wir, solange der Account aktiv
        ist bzw. gesetzliche Aufbewahrungsfristen gelten. Sie können Löschung verlangen, soweit
        keine Pflicht zur Aufbewahrung entgegensteht.
      </p>

      <h2>6. Ihre Rechte</h2>
      <p>
        Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerspruch,
        Beschwerde bei einer Aufsichtsbehörde. Kontakt: {CONTACT_EMAIL}
      </p>

      <h2>7. Cookies</h2>
      <p>
        Essenzielle Cookies für Session/Consent. Analytics nur nach Einwilligung über das
        Cookie-Banner der Plattform.
      </p>
    </article>
  );
}
