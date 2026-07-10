import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { LegalPageLayout } from "../components/LegalPageLayout";
import { Card } from "../components/ui";
import { fetchTrustCatalog } from "../lib/legalApi";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  "Vertrauen & Daten",
  "Transparenz: welche Daten Virtus Core sammelt, speichert und schützt.",
  "/trust"
);

function processorLabel(key: string) {
  const labels: Record<string, string> = {
    hosting: "Hosting",
    payment: "Zahlung",
    email: "E-Mail",
    ai: "KI-Dienste",
    analytics: "Analyse",
  };
  return labels[key] ?? key;
}

export default async function TrustPage() {
  const trust = await fetchTrustCatalog();
  const pending = trust ? !trust.publishable_datenschutz : true;

  return (
    <PublicPageShell>
      <LegalPageLayout
        title="Vertrauen & Daten"
        subtitle={`Transparenz bei ${BRAND_NAME} — keine Black Box`}
        pending={pending}
      >
        {!trust ? (
          <Card hover={false} padding="md" className="mt-4">
            <p className="text-sm text-genesis-muted">
              Trust-Katalog vorübergehend nicht verfügbar. Siehe{" "}
              <Link href="/datenschutz" className="text-genesis-accent hover:underline">
                Datenschutzerklärung
              </Link>
              .
            </p>
          </Card>
        ) : (
          <div className="mt-4 space-y-4">
            <Card hover={false} padding="md" className="border-genesis-accent/20 bg-genesis-accent/5">
              <h2 className="text-lg font-semibold text-white">Trust Checklist</h2>
              <p className="mt-1 text-sm text-genesis-muted">
                Das Wichtigste auf einen Blick — ohne Juristendeutsch.
              </p>
              <ul className="mt-4 space-y-4">
                {trust.trust_checklist.map((item) => (
                  <li key={item.id} className="flex gap-3 text-sm">
                    <span className="text-xl leading-none" aria-hidden>
                      {item.emoji}
                    </span>
                    <div>
                      <p className="font-medium text-white">{item.title}</p>
                      <p className="mt-1 leading-relaxed text-genesis-muted">{item.body}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>

            <Card hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">Ihre Daten — einfach erklärt</h2>
              <dl className="mt-4 space-y-4">
                {trust.data_storage_guide.map((item) => (
                  <div key={item.id}>
                    <dt className="text-sm font-medium text-white">{item.question}</dt>
                    <dd className="mt-1 text-sm leading-relaxed text-genesis-muted">{item.answer}</dd>
                  </div>
                ))}
              </dl>
            </Card>

            <Card hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">Welche Daten</h2>
              <ul className="mt-3 space-y-3 text-sm">
                {trust.data_collected.map((item) => (
                  <li key={item.id}>
                    <span className="font-medium text-white">{item.label}</span>
                    <span className="text-genesis-muted"> — {item.purpose}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">Speicherort & Aufbewahrung</h2>
              <p className="mt-2 text-sm text-genesis-muted">
                Speicherort: <strong className="text-white">{trust.storage_location}</strong>
              </p>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-genesis-muted">
                <li>Projektdaten: bis zu {trust.retention.project_days} Tage</li>
                <li>Technische Logs: {trust.retention.logs_days} Tage</li>
                <li>Bestell-/Rechnungsdaten: bis zu {trust.retention.order_days} Tage</li>
                <li>Löschung auf Anfrage: innerhalb von {trust.retention.deletion_request_days} Tagen</li>
              </ul>
            </Card>

            <Card hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">Wer hat Zugriff</h2>
              <p className="mt-2 text-sm text-genesis-muted">{trust.access.owner_team}</p>
              <ul className="mt-3 space-y-2 text-sm text-genesis-muted">
                {Object.entries(trust.access.processors).map(([key, providers]) => (
                  <li key={key}>
                    <span className="text-white">{processorLabel(key)}:</span>{" "}
                    {providers.length ? providers.join(", ") : "—"}
                  </li>
                ))}
              </ul>
              {trust.access.never_sold && (
                <p className="mt-4 rounded-lg border border-emerald-500/20 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-100/90">
                  Ihre personenbezogenen Daten werden <strong>nicht an Dritte verkauft</strong>.
                </p>
              )}
            </Card>

            <Card hover={false} padding="md">
              <h2 className="text-lg font-semibold text-white">Rechtliche Dokumente</h2>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <Link href="/datenschutz" className="text-genesis-accent hover:underline">
                    Datenschutzerklärung
                  </Link>
                </li>
                <li>
                  <Link href="/impressum" className="text-genesis-accent hover:underline">
                    Impressum
                  </Link>
                </li>
                <li>
                  <Link href="/cookies" className="text-genesis-accent hover:underline">
                    Cookie-Richtlinie
                  </Link>
                </li>
                <li>
                  <Link href="/ai-disclaimer" className="text-genesis-accent hover:underline">
                    KI-Hinweis
                  </Link>
                </li>
                <li>
                  <Link href="/intellectual-property" className="text-genesis-accent hover:underline">
                    Urheberrecht & Nutzungsrechte
                  </Link>
                </li>
              </ul>
            </Card>

            {trust.security_center_horizon.status === "architecture_only" && (
              <Card hover={false} padding="md">
                <h2 className="text-lg font-semibold text-white">Security Center</h2>
                <p className="mt-2 text-sm text-genesis-muted">
                  Geplant (Horizon): {trust.security_center_horizon.planned_modules.join(" · ")}
                </p>
              </Card>
            )}
          </div>
        )}
      </LegalPageLayout>
    </PublicPageShell>
  );
}
