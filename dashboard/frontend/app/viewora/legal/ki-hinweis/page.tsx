import type { Metadata } from "next";
import { CONTACT_EMAIL } from "../../../lib/siteConfig";

export const metadata: Metadata = {
  title: "KI-Hinweis",
  description: "Transparenz zu KI in Virtus Video AI — professioneller AI Video/Content Generator",
  robots: { index: true, follow: true },
};

export default function Virtus Video AIAiNoticePage() {
  return (
    <article className="Virtus Video AI-legal">
      <h1>KI-Hinweis</h1>
      <p>
        Virtus Video AI ist ein <strong>hochprofessioneller AI Content / Video Generator</strong> —
        betrieben als Studio-Produkt von Virtus Core.
      </p>

      <h2>Was Sie sehen</h2>
      <p>
        Eine Schaltfläche <strong>Create</strong> und ergebnisorientierte Werkzeuge (Modes,
        Visual DNA, Hook Lab, Viral Score, Product Mode, Content Machine). Sie wählen nicht
        einzelne KI-Modelle.
      </p>

      <h2>Was intern passiert</h2>
      <pre
        style={{
          background: "var(--vo-bg-elev)",
          padding: "1rem",
          borderRadius: 12,
          overflow: "auto",
          fontSize: "0.85rem",
          border: "1px solid var(--vo-line)",
        }}
      >{`USER
 ↓
AI ORCHESTRATOR
 ↓
wählt besten Pipeline
 ↓
IMAGE / VIDEO / VOICE / LLM / MUSIC / CAPTIONS
 ↓
FINAL PACKAGE`}</pre>

      <h2>Aktueller Leistungsstand</h2>
      <ul>
        <li>Creative Packages: Hooks, Skripte, Captions, Storyboard, Scores — live</li>
        <li>Generate 10, Hook Lab, Make it Better, Content Machine — live</li>
        <li>Vollständiger MP4-Render über Provider Gateway — wird angebunden, ohne
          Modell-Picker für Kunden</li>
        <li>Social-Analytics-Connect — Coming</li>
      </ul>

      <h2>Kennzeichnung</h2>
      <p>
        Generierte Texte und visuelle Vorschläge sind KI-gestützt. Bei Veröffentlichung in
        regulierten Kontexten sind Sie selbst für Kennzeichnungspflichten verantwortlich.
      </p>

      <h2>Kontakt</h2>
      <p>{CONTACT_EMAIL}</p>
    </article>
  );
}
