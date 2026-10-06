"use client";

import Link from "next/link";
import { OfficeShell } from "./OfficeShell";
import { useOfficeT } from "../../lib/useOfficeT";

/** Landing for Lebenslauf — routes into Bewerbung Office workflow. */
export function OfficeLebenslaufLanding() {
  const { t } = useOfficeT();

  return (
    <OfficeShell active="lebenslauf">
      <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
        <Link
          href="/office"
          className="rounded-lg border border-[var(--vo-border)] px-3 py-1.5 text-[var(--vo-ink)] hover:bg-black/[0.03]"
        >
          ← {t("back")}
        </Link>
        <Link
          href="/office"
          className="rounded-lg px-3 py-1.5 text-[var(--vo-muted)] underline-offset-2 hover:text-[var(--vo-ink)] hover:underline"
        >
          {t("cancel")}
        </Link>
      </div>
      <section className="vo-enter max-w-2xl">
        <h1 className="vo-display text-3xl font-semibold sm:text-4xl">
          {t("catalog.lebenslauf.title")}
        </h1>
        <p className="mt-3 text-[var(--vo-muted)]">{t("catalog.lebenslauf.subtitle")}</p>
        <dl className="mt-8 space-y-4 text-sm">
          <div>
            <dt className="font-semibold">{t("youUpload")}</dt>
            <dd className="text-[var(--vo-muted)]">{t("catalog.lebenslauf.upload")}</dd>
          </div>
          <div>
            <dt className="font-semibold">{t("youReceive")}</dt>
            <dd className="text-[var(--vo-muted)]">{t("catalog.lebenslauf.receive")}</dd>
          </div>
          <div className="flex gap-4">
            <span className="font-semibold text-[var(--vo-accent)]">
              {t("fromPrice", { price: t("catalog.lebenslauf.price") })}
            </span>
            <span className="text-[var(--vo-muted)]">
              {t("eta", { minutes: t("catalog.lebenslauf.eta") })}
            </span>
          </div>
        </dl>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/office/bewerbung"
            className="inline-flex min-h-[44px] items-center rounded-xl bg-[var(--vo-accent)] px-5 text-sm font-semibold text-white"
          >
            {t("actions.lebenslauf_create")}
          </Link>
          <Link
            href="/office/bewerbung"
            className="inline-flex min-h-[44px] items-center rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-5 text-sm font-semibold"
          >
            {t("actions.lebenslauf_improve")}
          </Link>
        </div>
        <p className="mt-4 text-xs text-[var(--vo-muted)]">{t("customerPayHint")}</p>
      </section>
    </OfficeShell>
  );
}
