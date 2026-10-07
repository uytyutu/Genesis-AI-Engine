import { formatAddress, impressumMissing, loadEntity, type LegalEntity } from "./entity";
import type { LegalDocument } from "./types";

type VirtusDoc = {
  id: string;
  title: string;
  subtitle?: string;
  publishable?: boolean;
  missing_fields?: string[];
  sections?: { heading: string; body: string }[];
};

async function fetchVirtusDoc(docId: string): Promise<LegalDocument | null> {
  const base = (
    process.env.ANON_LEGAL_SOURCE_URL ||
    process.env.GENESIS_PUBLIC_URL ||
    ""
  ).replace(/\/$/, "");
  if (!base) return null;
  try {
    const r = await fetch(`${base}/api/public/legal/documents/${docId}?locale=de`, {
      next: { revalidate: 3600 },
    });
    if (!r.ok) return null;
    const doc = (await r.json()) as VirtusDoc;
    if (!doc?.sections?.length) return null;
    return {
      id: docId,
      title: doc.title,
      subtitle: doc.subtitle || "",
      publishable: Boolean(doc.publishable),
      missingFields: doc.missing_fields || [],
      sections: doc.sections.map((s) => ({ heading: s.heading, body: s.body })),
      source: "virtus_api",
    };
  } catch {
    return null;
  }
}

function operatorBlock(e: LegalEntity): string {
  let body =
    `${e.full_name}\n` +
    `${e.trade_name || "ANON"}\n` +
    `${formatAddress(e)}\n\n` +
    `E-Mail: ${e.email}\n`;
  if (e.phone) body += `Telefon: ${e.phone}\n`;
  if (e.website) body += `Website: ${e.website}\n`;
  if (e.legal_form) body += `\nRechtsform: ${e.legal_form}\n`;
  if (e.handelsregister) {
    body += `Handelsregister: ${e.handelsregister}`;
    if (e.register_court) body += `, Registergericht: ${e.register_court}`;
    body += "\n";
  }
  if (e.managing_director) body += `Vertretungsberechtigt: ${e.managing_director}\n`;
  if (e.vat_id) body += `USt-IdNr.: ${e.vat_id}\n`;
  return body.trim();
}

function pendingDoc(id: string, title: string): LegalDocument {
  return {
    id,
    title,
    subtitle: "Angaben werden aus der bestehenden Legal Foundation geladen",
    publishable: false,
    missingFields: ["operator"],
    sections: [
      {
        heading: "Dokument in Vorbereitung",
        body:
          "Dieses Dokument wird aus den offiziellen Unternehmensdaten des Projekts geladen " +
          "(Virtus Legal API, GENESIS_LEGAL_* ENV oder content/legal/entity.json). " +
          "Es werden keine rechtlichen Angaben erfunden.",
      },
    ],
    source: "pending",
  };
}

function buildImpressum(e: LegalEntity, source: LegalDocument["source"]): LegalDocument {
  const missing = impressumMissing(e);
  if (missing.length) return pendingDoc("impressum", "Impressum");
  return {
    id: "impressum",
    title: "Impressum",
    subtitle: `Stand: ${e.documents_last_review} · Angaben gemäß § 5 DDG`,
    publishable: true,
    missingFields: [],
    source,
    sections: [
      { heading: "Anbieterkennzeichnung (§ 5 DDG)", body: operatorBlock(e) },
      {
        heading: "EU-Streitschlichtung",
        body:
          "Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: " +
          "https://ec.europa.eu/consumers/odr/",
      },
      {
        heading: "Verbraucherstreitbeilegung",
        body:
          "Wir sind nicht verpflichtet, an Streitbeilegungsverfahren vor einer " +
          "Verbraucherschlichtungsstelle teilzunehmen.",
      },
    ],
  };
}

function buildDatenschutz(e: LegalEntity, source: LegalDocument["source"]): LegalDocument {
  const missing = impressumMissing(e);
  if (missing.length) return pendingDoc("datenschutz", "Datenschutzerklärung");
  return {
    id: "datenschutz",
    title: "Datenschutzerklärung",
    subtitle: `Stand: ${e.documents_last_review}`,
    publishable: true,
    missingFields: [],
    source,
    sections: [
      {
        heading: "1. Verantwortlicher",
        body:
          `${e.full_name} — ${e.trade_name || "ANON"}\n${formatAddress(e)}\n` +
          `E-Mail: ${e.email}` +
          (e.phone ? `\nTelefon: ${e.phone}` : ""),
      },
      {
        heading: "2. Welche Daten wir verarbeiten",
        body:
          "• Kontodaten (E-Mail, Anzeigename, Passwort-Hash)\n" +
          "• Inhalte von Momenten/Gifts und Spielräumen (Nachrichten, Antworten, Medien)\n" +
          "• Anonyme öffentliche IDs (z. B. ANON #xxxxx) — keine Anzeige von E-Mail/IP an Empfänger\n" +
          "• Zahlungsdaten über Zahlungsdienstleister (Stripe; keine vollständigen Kartendaten bei uns)\n" +
          "• Technische Logdaten (IP, Browser, Zeitstempel) zur Sicherheit und Missbrauchsprävention\n" +
          "• Spielstatistiken (XP, Rang, Raumteilnahmen)",
      },
      {
        heading: "3. Zwecke der Verarbeitung",
        body:
          "• Bereitstellung der ANON-Plattform (Momente, anonyme Chats, Social Games)\n" +
          "• Vertragserfüllung und Zahlungsabwicklung\n" +
          "• Sicherheit, Moderations- und Missbrauchsschutz\n" +
          "• Gesetzliche Aufbewahrungspflichten",
      },
      {
        heading: "4. Speicherort und Aufbewahrung",
        body: `Speicherort: ${e.data_location}\nBestell-/Zahlungsnachweise werden gesetzlich vorgeschrieben aufbewahrt.`,
      },
      {
        heading: "5. Ihre Rechte",
        body:
          "Sie haben Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit " +
          "und Widerspruch nach DSGVO. Kontakt: " +
          (e.dpo_email || e.email) +
          `\n\nAufsichtsbehörde: ${e.supervisory_authority}`,
      },
      {
        heading: "6. Weitergabe",
        body:
          "Daten werden nicht verkauft. Weitergabe nur an erforderliche Dienstleister " +
          "(z. B. Hosting, Stripe) oder bei gesetzlicher Pflicht.",
      },
    ],
  };
}

function buildCookies(e: LegalEntity, source: LegalDocument["source"]): LegalDocument {
  return {
    id: "cookies",
    title: "Cookie-Richtlinie",
    subtitle: `Stand: ${e.documents_last_review || "2026-07"}`,
    publishable: !impressumMissing(e).length,
    missingFields: impressumMissing(e),
    source: impressumMissing(e).length ? "pending" : source,
    sections: [
      {
        heading: "Essenzielle Cookies",
        body:
          "• Sitzung / Session (anon_session) — Anmeldung und Sicherheit\n" +
          "• Sprachpräferenz (lokal im Browser, anon_locale)",
      },
      {
        heading: "Analytics / Marketing",
        body:
          "Derzeit keine Marketing-Cookies. Interne, nicht-invasive Event-Logs können serverseitig " +
          "ohne Third-Party-Tracker gespeichert werden.",
      },
      {
        heading: "Kontakt",
        body: e.email
          ? `Fragen zu Cookies: ${e.email}`
          : "Kontakt siehe Impressum, sobald Anbieterdaten geladen sind.",
      },
    ],
  };
}

function buildAgb(e: LegalEntity, source: LegalDocument["source"]): LegalDocument {
  const missing = impressumMissing(e);
  if (missing.length) return pendingDoc("agb", "Allgemeine Geschäftsbedingungen (AGB)");
  return {
    id: "agb",
    title: "Allgemeine Geschäftsbedingungen (AGB)",
    subtitle: `Stand: ${e.documents_last_review}`,
    publishable: true,
    missingFields: [],
    source,
    sections: [
      {
        heading: "1. Anbieter",
        body: operatorBlock(e),
      },
      {
        heading: "2. Leistungsgegenstand",
        body:
          "ANON bietet digitale emotionale Momente (Gifts), anonyme Kommunikation sowie " +
          " Social-Gaming-Räume als digitale Dienstleistungen an. Es handelt sich um digitale Inhalte/" +
          "Dienste — kein physischer Versand.",
      },
      {
        heading: "3. Preise und Zahlung",
        body:
          "Preise werden im Checkout in EUR angezeigt. Zahlung erfolgt über Stripe. " +
          "Der Vertrag kommt mit erfolgreicher Zahlungsbestätigung zustande. " +
          "Preis-Snapshots werden in der Bestellung gespeichert.",
      },
      {
        heading: "4. Nutzung und Missbrauch",
        body:
          "Belästigung, Spam, illegale Inhalte und Umgehung von Sicherheitsmaßnahmen sind untersagt. " +
          "Wir können Inhalte entfernen, Identitäten sperren und Konten einschränken.",
      },
      {
        heading: "5. Anonymität und Reveal",
        body:
          "Anonyme Funktionen zeigen Empfängern nur öffentliche ANON-IDs. " +
          "Ein Reveal erfolgt nur nach Freigabe/Zahlung gemäß Produktmechanik und nur, " +
          "wenn eine echte Identität systemseitig vorhanden ist.",
      },
      {
        heading: "6. Haftung",
        body:
          "Für unentgeltliche Bereiche haften wir nur bei Vorsatz und grober Fahrlässigkeit, " +
          "soweit gesetzlich zulässig. Nutzerinhalte liegen in der Verantwortung der Nutzer.",
      },
      {
        heading: "7. Kontakt",
        body: `E-Mail: ${e.email}`,
      },
    ],
  };
}

export async function getLegalDocument(
  docId: "impressum" | "datenschutz" | "cookies" | "agb"
): Promise<LegalDocument> {
  // Prefer live Virtus legal docs when publishable (same operator, no invented data).
  const remote = await fetchVirtusDoc(docId);
  if (remote?.publishable) return remote;

  const { entity, source } = loadEntity();
  switch (docId) {
    case "impressum":
      return buildImpressum(entity, source);
    case "datenschutz":
      return buildDatenschutz(entity, source);
    case "cookies":
      return buildCookies(entity, source);
    case "agb":
      return buildAgb(entity, source);
  }
}
