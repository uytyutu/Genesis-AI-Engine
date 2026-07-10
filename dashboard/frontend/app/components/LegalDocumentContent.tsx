import { Card } from "./ui";
import type { LegalDocument } from "../lib/legalApi";

function linkifyBody(body: string) {
  const parts = body.split(/(https?:\/\/[^\s]+)/g);
  return parts.map((part, i) =>
    /^https?:\/\//.test(part) ? (
      <a
        key={i}
        href={part}
        className="text-genesis-accent hover:underline"
        rel="noopener noreferrer"
        target="_blank"
      >
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export function LegalDocumentContent({ doc }: { doc: LegalDocument }) {
  return (
    <>
      {doc.disclaimer ? (
        <p className="mt-4 text-xs text-genesis-muted/80">{doc.disclaimer}</p>
      ) : null}
      <div className="mt-4 space-y-4">
        {doc.sections.map((section) => (
          <Card key={section.heading} hover={false} padding="md">
            <h2 className="text-lg font-semibold text-white">{section.heading}</h2>
            <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-genesis-muted">
              {linkifyBody(section.body)}
            </p>
          </Card>
        ))}
      </div>
    </>
  );
}
