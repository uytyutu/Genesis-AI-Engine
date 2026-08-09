import { PublicPageShell } from "./PublicPageShell";
import { LegalPageLayout } from "./LegalPageLayout";
import { LegalDocumentContent } from "./LegalDocumentContent";
import { Card } from "./ui";
import { fetchLegalDocument } from "../lib/legalApi";

export async function LegalDocumentPage({
  docId,
  fallbackTitle,
  fallbackSubtitle,
}: {
  docId: string;
  fallbackTitle: string;
  fallbackSubtitle?: string;
}) {
  const doc = await fetchLegalDocument(docId);

  if (!doc) {
    return (
      <PublicPageShell>
        <LegalPageLayout title={fallbackTitle} subtitle={fallbackSubtitle}>
          <Card hover={false} padding="md" className="mt-4 space-y-4">
            <p className="text-sm leading-relaxed text-genesis-muted">
              Ausführliche Informationen zur Nutzung künstlicher Intelligenz werden in Kürze
              veröffentlicht. Bei Fragen kontaktieren Sie uns gerne — wir erklären transparent,
              wie KI bei der Entwicklung Ihres Projekts eingesetzt wird.
            </p>
            <p className="text-sm text-genesis-muted">
              <a href="/kontakt" className="text-genesis-accent hover:underline">
                Kontakt aufnehmen
              </a>
            </p>
          </Card>
        </LegalPageLayout>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <LegalPageLayout
        title={doc.title}
        subtitle={doc.subtitle || fallbackSubtitle}
        pending={!doc.publishable}
      >
        <LegalDocumentContent doc={doc} />
      </LegalPageLayout>
    </PublicPageShell>
  );
}
