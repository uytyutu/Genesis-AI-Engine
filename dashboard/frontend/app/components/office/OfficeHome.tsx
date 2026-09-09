"use client";

import Link from "next/link";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";

const PERSONAL = [
  { id: "pdf_pro", href: "/office/pdf-pro", mark: "PDF" },
  { id: "cv_bewerbung", href: "/office/cv-bewerbung", mark: "CV" },
  { id: "translation_pack", href: "/office/translation-pack", mark: "A↔B" },
] as const;

const BUSINESS = [
  { id: "sales_kit", href: "/office/sales-kit", mark: "B2B" },
] as const;

const TOOLS = [{ id: "qr_code", href: "/office/qr", mark: "QR" }] as const;

const SINGLE_SERVICES = [
  { id: "searchable", href: "/office/searchable" },
  { id: "redaction", href: "/office/redaction" },
  { id: "fillable", href: "/office/fillable" },
  { id: "pdfa", href: "/office/pdfa" },
  { id: "archive", href: "/office/archive" },
  { id: "translate", href: "/office/translate" },
  { id: "documents", href: "/office/documents" },
  { id: "excel", href: "/office/excel" },
  { id: "lebenslauf", href: "/office/lebenslauf" },
  { id: "bewerbung", href: "/office/bewerbung" },
] as const;

const COMING_SOON = ["company_profile", "document_cleanup_pack", "process_sop_pack"] as const;

export function OfficeHome() {
  const { t } = useOfficeT();

  return (
    <OfficeShell active="home">
      <section className="vo-enter grid items-end gap-8 border-b border-[var(--vo-border)] pb-10 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <h1 className="vo-display max-w-2xl text-5xl font-semibold tracking-[-0.035em] text-[var(--vo-ink)] sm:text-6xl">
            {t("home.title")}
          </h1>
          <p className="mt-4 max-w-2xl text-xl leading-relaxed text-[var(--vo-muted)]">
            {t("home.taglineAds")}
          </p>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[var(--vo-ink)]/85">
            {t("home.lead")}
          </p>
        </div>
        <div className="rounded-2xl bg-[var(--vo-ink)] p-6 text-white shadow-[0_18px_44px_rgba(24,32,51,0.16)]">
          <p className="text-lg font-semibold">{t("home.smartTitle")}</p>
          <p className="mt-2 text-sm leading-relaxed text-white/72">{t("home.smartLead")}</p>
          <Link
            href="/office/smart"
            className="mt-5 inline-flex min-h-[48px] items-center justify-center rounded-xl bg-white px-5 text-sm font-semibold text-[var(--vo-ink)] transition hover:-translate-y-0.5"
          >
            {t("home.smartCta")} →
          </Link>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="vo-display text-3xl font-semibold">{t("home.packagesTitle")}</h2>
        <PackageGroup title={t("home.forPersonal")} items={PERSONAL} />
        <PackageGroup title={t("home.forBusiness")} items={BUSINESS} />
        <PackageGroup title={t("home.tools")} items={TOOLS} free />
      </section>

      <section className="mt-14 border-t border-[var(--vo-border)] pt-9">
        <details className="group">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-lg font-semibold text-[var(--vo-ink)]">
            {t("home.aLaCarteTitle")}
            <span className="text-[var(--vo-accent)] transition group-open:rotate-45">+</span>
          </summary>
          <div className="mt-5 flex flex-wrap gap-2">
            {SINGLE_SERVICES.map((service) => (
              <Link
                key={service.id}
                href={service.href}
                className="rounded-full border border-[var(--vo-border)] bg-[var(--vo-surface)] px-4 py-2 text-sm font-medium text-[var(--vo-ink)] transition hover:border-[var(--vo-accent)] hover:text-[var(--vo-accent)]"
              >
                {t(`catalog.${service.id}.title`)}
              </Link>
            ))}
          </div>
        </details>
      </section>

      <section className="mt-14 border-t border-[var(--vo-border)] pt-9">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--vo-muted)]">
              {t("home.b2bTitle")}
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-[var(--vo-muted)]">{t("home.b2bLead")}</p>
          </div>
          <span className="rounded-full border border-[var(--vo-border)] px-3 py-1 text-xs font-semibold text-[var(--vo-muted)]">
            {t("home.comingSoon")}
          </span>
        </div>
        <div className="mt-5 grid gap-px overflow-hidden rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-border)] sm:grid-cols-3">
          {COMING_SOON.map((id) => (
            <div key={id} className="bg-[var(--vo-surface)] p-5">
              <h3 className="font-semibold text-[var(--vo-ink)]">{t(`catalog.${id}.title`)}</h3>
              <p className="mt-2 text-xs leading-relaxed text-[var(--vo-muted)]">
                {t(`catalog.${id}.subtitle`)}
              </p>
            </div>
          ))}
        </div>
      </section>
    </OfficeShell>
  );
}

function PackageGroup({
  title,
  items,
  free = false,
}: {
  title: string;
  items: ReadonlyArray<{ id: string; href: string; mark: string }>;
  free?: boolean;
}) {
  const { t } = useOfficeT();
  return (
    <div className="mt-8">
      <h3 className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--vo-muted)]">{title}</h3>
      <div
        className={`mt-3 grid gap-px overflow-hidden rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-border)] ${
          items.length > 1 ? "md:grid-cols-3" : ""
        }`}
      >
        {items.map((item) => (
          <Link
            key={item.id}
            href={item.href}
            className="group flex min-h-56 flex-col bg-[var(--vo-surface)] p-6 transition hover:bg-[var(--vo-accent-soft)]/55"
          >
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm font-bold tracking-tight text-[var(--vo-accent)]">{item.mark}</span>
              {free ? (
                <span className="rounded-full bg-[var(--vo-ok)] px-2.5 py-1 text-[10px] font-bold text-white">
                  {t("home.free")}
                </span>
              ) : null}
            </div>
            <h4 className="vo-display mt-8 text-2xl font-semibold text-[var(--vo-ink)]">
              {t(`catalog.${item.id}.title`)}
            </h4>
            <p className="mt-2 text-sm leading-relaxed text-[var(--vo-muted)]">
              {t(`catalog.${item.id}.subtitle`)}
            </p>
            <div className="mt-auto flex items-end justify-between gap-3 pt-6">
              <div>
                <p className="text-lg font-bold text-[var(--vo-ink)]">
                  {free
                    ? t("home.free")
                    : item.id === "sales_kit"
                      ? t("fromPrice", { price: t(`catalog.${item.id}.price`) })
                      : t(`catalog.${item.id}.price`)}
                </p>
                <p className="text-xs text-[var(--vo-muted)]">{free ? t("qr.freeBadge") : t("home.oneTime")}</p>
              </div>
              <span className="font-semibold text-[var(--vo-accent)] transition group-hover:translate-x-1">
                {t("start")} →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
