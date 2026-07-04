import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Kontakt",
  "Связаться с Genesis: email и форма заказа.",
  "/kontakt"
);

export default function KontaktPage() {
  return (
    <PublicPageShell>
      <main className="mx-auto max-w-xl text-center">
        <h1 className="text-3xl font-bold">Kontakt</h1>
        <p className="mt-3 text-genesis-muted">
          Вопросы по заказу, статусу или сотрудничеству — напишите нам.
        </p>
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="mt-8 inline-block rounded-2xl border border-genesis-accent/40 bg-genesis-accent/10 px-8 py-4 text-lg font-semibold text-genesis-accent hover:bg-genesis-accent/20"
        >
          {CONTACT_EMAIL}
        </a>
        <p className="mt-10 text-sm text-genesis-muted">
          Готовы заказать сайт?{" "}
          <Link href="/order" className="text-genesis-accent hover:underline">
            Перейти к форме заказа →
          </Link>
        </p>
      </main>
    </PublicPageShell>
  );
}
