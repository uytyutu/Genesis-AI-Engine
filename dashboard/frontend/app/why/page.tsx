import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Warum günstiger als Agenturen? · ${BRAND_NAME}`,
  `Website ab 299 € statt typischer Agenturpreise ab 1 500–5 000 €. Schneller Start, eigenes Panel, eine Plattform — ohne unbelegbare Versprechen.`,
  "/why"
);

const ROWS: { agency: string; virtus: string }[] = [
  { agency: "Ab 1 500–5 000 €", virtus: "Ab 299 €" },
  { agency: "Langer Entwicklungszyklus", virtus: "Schneller Start" },
  { agency: "Jede Änderung über den Manager", virtus: "Selbst steuern über das Panel" },
  { agency: "Getrennte Auftragnehmer", virtus: "Eine Plattform" },
];

export default function WhyPage() {
  return (
    <PublicPageShell>
      <main className="mx-auto max-w-3xl px-4 py-12 text-zinc-100">
        <p className="text-xs uppercase tracking-[0.25em] text-emerald-300/80">
          {BRAND_NAME}
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">
          Warum günstiger als Agenturen?
        </h1>
        <p className="mt-3 text-sm text-zinc-400">
          Nur Unterschiede, die wir belegen können — keine unbelegbaren Versprechen.
          Für Kunden gibt es nur {BRAND_NAME}, keine interne Entwicklungs-Sprache.
        </p>

        <div className="mt-8 overflow-x-auto rounded-2xl border border-white/10 bg-black/30">
          <table className="w-full min-w-[28rem] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-white/15 text-xs uppercase tracking-wider text-zinc-500">
                <th className="px-4 py-3 font-semibold">Agentur</th>
                <th className="px-4 py-3 font-semibold text-emerald-200">
                  {BRAND_NAME}
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row.agency} className="border-b border-white/10 last:border-0">
                  <td className="px-4 py-3 text-zinc-400">{row.agency}</td>
                  <td className="px-4 py-3 font-medium text-white">{row.virtus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-[11px] text-zinc-600">
          Preisrahmen Agentur: typische Marktspanne für individuelle Websites — nicht als
          Angebot eines konkreten Anbieters gemeint. Virtus Core: Website-Pakete Basic 299 € ·
          Business 599 € · Premium 999 €. Online Store ist ein eigenes Produkt.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/site#pricing"
            className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-bold text-black hover:brightness-110"
          >
            Website-Pakete ansehen →
          </Link>
          <Link
            href="/site#ai-store"
            className="rounded-xl border border-white/15 px-5 py-2.5 text-sm text-zinc-200 hover:bg-white/5"
          >
            AI Store ansehen
          </Link>
          <Link
            href="/site"
            className="rounded-xl border border-white/15 px-5 py-2.5 text-sm text-zinc-200 hover:bg-white/5"
          >
            Zur Startseite
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}
