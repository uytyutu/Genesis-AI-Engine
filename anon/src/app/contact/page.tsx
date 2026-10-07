import type { Metadata } from "next";
import Link from "next/link";
import { getLegalDocument } from "@/lib/legal/documents";

export const metadata: Metadata = {
  title: "Contact",
  description: "Contact ANON support.",
};

export default async function ContactPage() {
  const impressum = await getLegalDocument("impressum");
  const emailSection = impressum.sections.find((s) =>
    s.body.toLowerCase().includes("e-mail")
  );
  const emailMatch = emailSection?.body.match(/E-Mail:\s*(\S+)/i);

  return (
    <main className="anon-card anim-in mx-auto max-w-lg p-6">
      <nav className="mb-4 text-sm anon-muted">
        <Link href="/">← ANON</Link>
      </nav>
      <h1 className="text-2xl font-semibold">Contact</h1>
      <p className="mt-3 text-sm anon-muted">
        Support for moments, anonymous chat, and social games.
      </p>
      {emailMatch ? (
        <p className="mt-6 text-lg">
          <a className="text-sky-300 underline" href={`mailto:${emailMatch[1]}`}>
            {emailMatch[1]}
          </a>
        </p>
      ) : (
        <p className="mt-6 text-sm">
          See <Link className="underline" href="/impressum">Impressum</Link> for operator
          contact once legal data is loaded.
        </p>
      )}
      <Link href="/help" className="anon-btn anon-btn-ghost mt-6 inline-flex">
        Help
      </Link>
    </main>
  );
}
