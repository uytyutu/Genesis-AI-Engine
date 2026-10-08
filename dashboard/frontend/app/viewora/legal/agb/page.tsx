import type { Metadata } from "next";
import { CONTACT_EMAIL } from "../../../lib/siteConfig";

export const metadata: Metadata = {
  title: "AGB",
  description: "Allgemeine Geschäftsbedingungen Virtus Video AI",
  robots: { index: true, follow: true },
};

export default function Virtus Video AITermsPage() {
  return (
    <article className="Virtus Video AI-legal">
      <h1>AGB — Virtus Video AI</h1>
      <p>Allgemeine Geschäftsbedingungen für das AI Content Studio Virtus Video AI</p>

      <h2>1. Gegenstand</h2>
      <p>
        Virtus Video AI ist ein professioneller KI-Content-Dienst: Erstellung von Creative Packages
        (Hooks, Skripte, Captions, Storyboards, Viral Scores, Pläne) und — sobald live —
        gerenderten Video-Exports über die Studio-Orchestrierung. Es handelt sich nicht um
        einen einfachen „Modell-Zugang“, sondern um ein ergebnisorientiertes Content Studio.
      </p>

      <h2>2. Vertragspartner & Preise</h2>
      <p>
        Anbieter ist der im Impressum genannte Diensteanbieter. Preise: FREE (3 Creations),
        CREATOR €12.99/Mo, PRO €29.99/Mo, BUSINESS €59.99/Mo, STUDIO €149/Mo sowie Credit
        Packs (€5 / €15 / €30 / €100). Es gelten die zum Bestellzeitpunkt angezeigten Preise.
      </p>

      <h2>3. Credits & Fair Use</h2>
      <p>
        Credits sind interne Verbrauchseinheiten. Unterschiedliche Aktionen können
        unterschiedliche Credits kosten. Missbrauch, Scraping oder Umgehung von Limits ist
        untersagt. Ungenutzte Pack-Credits verfallen nicht; Abo-Credits erneuern sich mit dem
        Abrechnungszeitraum gemäß Planbeschreibung.
      </p>

      <h2>4. Zahlung</h2>
      <p>
        Zahlung über Stripe Checkout. In Test-/Demo-Umgebungen kann ein gekennzeichnetes Demo
        Payment (payment_mode=demo) genutzt werden — dieses erzeugt keinen echten Umsatz.
      </p>

      <h2>5. Ergebnisse & KI</h2>
      <p>
        KI-Ausgaben können Fehler enthalten. Der Kunde prüft Inhalte vor Veröffentlichung
        (Marken-, Urheber-, Wettbewerbs- und Plattformregeln). Virtus Video AI liefert keine
        Rechtsberatung.
      </p>

      <h2>6. Nutzungsrechte</h2>
      <p>
        Mit gültigem bezahltem Plan (nicht FREE) erhält der Kunde ein einfaches Recht zur
        kommerziellen Nutzung der für ihn erzeugten Content-Pakete, soweit keine Rechte Dritter
        (Uploads, Musik, Personen) entgegenstehen. Der Kunde bleibt für seine Uploads
        verantwortlich.
      </p>

      <h2>7. Haftung</h2>
      <p>
        Haftung für Vorsatz und grobe Fahrlässigkeit unbeschränkt; im Übrigen nach
        gesetzlichen Vorschriften. Für unentgeltliche FREE-Nutzung ist die Haftung auf Vorsatz
        und grobe Fahrlässigkeit beschränkt.
      </p>

      <h2>8. Widerruf (Verbraucher)</h2>
      <p>
        Verbraucher haben ein Widerrufsrecht nach Fernabsatzrecht. Bei digitalen Inhalten kann
        das Widerrufsrecht erlöschen, wenn die Ausführung mit ausdrücklicher Zustimmung vor
        Ablauf der Frist begonnen hat. Kontakt: {CONTACT_EMAIL}
      </p>

      <h2>9. Schlussbestimmungen</h2>
      <p>
        Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.
        Gerichtsstand — soweit zulässig — am Sitz des Anbieters.
      </p>
    </article>
  );
}
