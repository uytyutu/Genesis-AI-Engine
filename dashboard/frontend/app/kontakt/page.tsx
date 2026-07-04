import type { Metadata } from "next";
import { PublicPageShell } from "../components/PublicPageShell";
import { PublicPageHero } from "../components/PublicPageHero";
import { ButtonLink, Card } from "../components/ui";
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
      <PublicPageHero
        title="Kontakt"
        description="Вопросы по заказу, статусу или сотрудничеству — напишите нам."
      />
      <Card glow className="mx-auto max-w-xl text-center" padding="lg">
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="text-lg font-semibold text-genesis-accent transition-smooth hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/70 rounded-lg px-2"
        >
          {CONTACT_EMAIL}
        </a>
        <p className="mt-8 text-sm text-genesis-muted">
          Готовы заказать сайт?
        </p>
        <ButtonLink href="/order" variant="primary" size="md" className="mt-4">
          Перейти к форме заказа →
        </ButtonLink>
      </Card>
    </PublicPageShell>
  );
}
