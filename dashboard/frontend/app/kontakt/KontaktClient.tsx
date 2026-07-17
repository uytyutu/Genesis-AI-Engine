"use client";

import { PublicPageShell } from "../components/PublicPageShell";
import { PublicPageHero } from "../components/PublicPageHero";
import { ButtonLink, Card } from "../components/ui";
import { CONTACT_EMAIL } from "../lib/siteConfig";
import { useTranslation } from "react-i18next";
import { useLocale } from "../context/LocaleContext";

export function KontaktClient() {
  const { t } = useTranslation("site");
  const { uiLocale } = useLocale();
  const subject =
    uiLocale === "de"
      ? "Support · Virtus Core Landing Page"
      : uiLocale === "ru"
        ? "Поддержка · Virtus Core Landing"
        : "Support · Virtus Core Landing";

  return (
    <PublicPageShell>
      <PublicPageHero title={t("kontakt.title")} description={t("kontakt.description")} />
      <Card glow className="mx-auto max-w-xl text-center" padding="lg">
        <a
          href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}`}
          className="text-lg font-semibold text-genesis-accent transition-smooth hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/70 rounded-lg px-2"
        >
          {CONTACT_EMAIL}
        </a>
        <p className="mt-3 text-xs text-genesis-muted">
          {uiLocale === "de"
            ? "Wir antworten auf Deutsch."
            : uiLocale === "ru"
              ? "Для рынка DE поддержка отвечает на немецком; UI можно переключить."
              : "For the DE market we reply in German."}
        </p>
        <p className="mt-8 text-sm text-genesis-muted">{t("kontakt.ready")}</p>
        <ButtonLink href="/order" variant="primary" size="md" className="mt-4">
          {t("kontakt.cta")}
        </ButtonLink>
      </Card>
    </PublicPageShell>
  );
}
