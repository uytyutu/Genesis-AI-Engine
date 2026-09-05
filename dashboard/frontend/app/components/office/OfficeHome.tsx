"use client";

import Link from "next/link";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";

/** Commercial cards — only SKUs with executor today (no official/legal theatre). */
const SERVICE_CARDS = [
  {
    id: "smart",
    href: "/office/smart",
    icon: "✨",
    featured: true,
  },
  { id: "quality", href: "/office/smart", icon: "🔎" },
  { id: "translate", href: "/office/translate", icon: "🌍" },
  { id: "documents", href: "/office/documents", icon: "📄" },
  { id: "excel", href: "/office/excel", icon: "📊" },
  { id: "lebenslauf", href: "/office/lebenslauf", icon: "🧾" },
  { id: "bewerbung", href: "/office/bewerbung", icon: "💼" },
] as const;

const QUICK_CTAS = [
  { id: "upload", href: "/office/smart" },
  { id: "quality", href: "/office/smart" },
  { id: "translate", href: "/office/translate" },
  { id: "create", href: "/office/documents" },
  { id: "excel", href: "/office/excel" },
  { id: "cv", href: "/office/lebenslauf" },
  { id: "bewerbung", href: "/office/bewerbung" },
] as const;

const HOW_STEPS = [1, 2, 3, 4, 5, 6, 7, 8] as const;

/**
 * Client vitrine = sellable-only cards above.
 * Unfinished B2B document products stay in backend SSOT / `/api/office/status` only —
 * never on `/office` until executor + validator + E2E PASS.
 */

export function OfficeHome() {
  const { t } = useOfficeT();

  return (
    <OfficeShell active="home">
      <section className="vo-enter max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--vo-accent)]">
          {t("home.eyebrow")}
        </p>
        <h1 className="vo-display mt-2 text-4xl font-semibold tracking-tight text-[var(--vo-ink)] sm:text-5xl">
          {t("home.title")}
        </h1>
        <p className="mt-3 text-lg text-[var(--vo-muted)]">{t("home.subtitle")}</p>
        <p className="mt-4 text-sm leading-relaxed text-[var(--vo-ink)]/90">
          {t("home.lead")}
        </p>
      </section>

      <div className="vo-enter mt-8 rounded-2xl border border-dashed border-[var(--vo-accent)]/35 bg-[var(--vo-accent-soft)]/55 px-5 py-6 sm:px-7">
        <h2 className="text-lg font-semibold text-[var(--vo-ink)]">{t("home.smartTitle")}</h2>
        <p className="mt-2 text-sm text-[var(--vo-muted)]">{t("home.smartLead")}</p>
        <Link
          href="/office/smart"
          className="mt-5 inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[var(--vo-accent)] px-6 text-sm font-semibold text-white hover:brightness-110"
        >
          {t("home.smartCta")}
        </Link>
        <p className="mt-3 text-xs text-[var(--vo-muted)]">{t("ocrHonesty")}</p>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {QUICK_CTAS.map((c) => (
          <Link
            key={c.id}
            href={c.href}
            className="rounded-full border border-[var(--vo-border)] bg-[var(--vo-surface)] px-3 py-1.5 text-xs font-medium text-[var(--vo-ink)] hover:border-[var(--vo-accent)]/40"
          >
            {t(`home.quick.${c.id}`)}
          </Link>
        ))}
      </div>

      <section className="mt-12 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--vo-muted)]">
          {t("home.servicesTitle")}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {SERVICE_CARDS.map((card, i) => (
            <Link
              key={card.id}
              href={card.href}
              className={`vo-enter group rounded-2xl border p-5 shadow-[0_8px_24px_rgba(24,32,51,0.04)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(26,79,140,0.08)] ${
                "featured" in card && card.featured
                  ? "border-[var(--vo-accent)]/35 bg-[var(--vo-accent-soft)]/40"
                  : "border-[var(--vo-border)] bg-[var(--vo-surface)] hover:border-[var(--vo-accent)]/35"
              }`}
              style={{ animationDelay: `${60 + i * 30}ms` }}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl" aria-hidden>
                  {card.icon}
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg font-semibold text-[var(--vo-ink)]">
                    {t(`catalog.${card.id}.title`)}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--vo-muted)]">
                    {t(`catalog.${card.id}.subtitle`)}
                  </p>
                  <dl className="mt-4 space-y-2 text-xs text-[var(--vo-muted)]">
                    <div>
                      <dt className="font-semibold text-[var(--vo-ink)]/80">{t("youUpload")}</dt>
                      <dd>{t(`catalog.${card.id}.upload`)}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-[var(--vo-ink)]/80">{t("youReceive")}</dt>
                      <dd>{t(`catalog.${card.id}.receive`)}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-[var(--vo-ink)]/80">
                        {t("home.formatsLabel")}
                      </dt>
                      <dd>{t(`catalog.${card.id}.formats`)}</dd>
                    </div>
                  </dl>
                  <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">
                    <span className="font-semibold text-[var(--vo-accent)]">
                      {t("fromPrice", { price: t(`catalog.${card.id}.price`) })}
                    </span>
                    <span className="text-[var(--vo-muted)]">
                      {t("eta", { minutes: t(`catalog.${card.id}.eta`) })}
                    </span>
                    <span className="ml-auto text-[var(--vo-accent)] opacity-0 transition group-hover:opacity-100">
                      {t("start")} →
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="vo-enter mt-14 rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6 sm:p-8">
        <h2 className="vo-display text-2xl font-semibold text-[var(--vo-ink)]">
          {t("home.howTitle")}
        </h2>
        <ol className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {HOW_STEPS.map((n) => (
            <li
              key={n}
              className="rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-3 text-sm"
            >
              <span className="font-bold text-[var(--vo-accent)]">{n}.</span>{" "}
              <span className="font-semibold text-[var(--vo-ink)]">
                {t(`home.how.${n}.title`)}
              </span>
              <p className="mt-1 text-xs text-[var(--vo-muted)]">{t(`home.how.${n}.body`)}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-10 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5 text-sm">
          <h3 className="font-semibold text-[var(--vo-ink)]">{t("footer.privacyTitle")}</h3>
          <p className="mt-2 text-[var(--vo-muted)]">{t("footer.privacyBody")}</p>
        </div>
        <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5 text-sm">
          <h3 className="font-semibold text-[var(--vo-ink)]">{t("footer.legalTitle")}</h3>
          <p className="mt-2 text-[var(--vo-muted)]">{t("footer.legalBody")}</p>
        </div>
      </section>

      <div className="mt-10 text-center">
        <Link
          href="/office/smart"
          className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[var(--vo-accent)] px-8 text-sm font-semibold text-white hover:brightness-110"
        >
          {t("home.smartCta")}
        </Link>
      </div>
    </OfficeShell>
  );
}
