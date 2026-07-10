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
          <Card hover={false} padding="md" className="mt-4">
            <p className="text-sm text-genesis-muted">
              Dokument vorübergehend nicht verfügbar. Bitte später erneut versuchen oder{" "}
              <a href="/kontakt" className="text-genesis-accent hover:underline">
                Kontakt
              </a>
              .
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
