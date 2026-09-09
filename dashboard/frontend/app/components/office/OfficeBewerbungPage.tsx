"use client";

import { VirtusBewerbungStorefront } from "../storefront/VirtusBewerbungStorefront";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";

export function OfficeBewerbungPage({ packageMode = false }: { packageMode?: boolean }) {
  const { t } = useOfficeT();
  return (
    <OfficeShell active={packageMode ? "cv_bewerbung" : "bewerbung"}>
      {packageMode ? (
        <section className="vo-enter mb-10 border-b border-[var(--vo-border)] pb-8">
          <h1 className="vo-display text-4xl font-semibold tracking-tight text-[var(--vo-ink)]">
            {t("catalog.cv_bewerbung.title")}
          </h1>
          <p className="mt-3 max-w-2xl text-[var(--vo-muted)]">
            {t("catalog.cv_bewerbung.subtitle")}
          </p>
          <p className="mt-3 text-sm font-semibold text-[var(--vo-accent)]">
            {t("catalog.cv_bewerbung.price")} · {t("home.oneTime")}
          </p>
        </section>
      ) : null}
      <VirtusBewerbungStorefront
        embedded
        defaultAction={packageMode ? "bewerbung_paket" : "lebenslauf_create"}
      />
    </OfficeShell>
  );
}
