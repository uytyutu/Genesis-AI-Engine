import { LEGAL_PENDING } from "../lib/siteConfig";

export function LegalProse({ children }: { children: React.ReactNode }) {
  return (
    <article className="prose-legal mx-auto max-w-3xl">
      {LEGAL_PENDING && (
        <div
          className="mb-8 rounded-xl border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-100/90"
          role="status"
        >
          Einige Pflichtangaben werden nach Abschluss der Gewerbeanmeldung ergänzt.
        </div>
      )}
      {children}
    </article>
  );
}
