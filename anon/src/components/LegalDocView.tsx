"use client";

import Link from "next/link";
import type { LegalDocument } from "@/lib/legal/types";
import { useI18n } from "@/components/I18nProvider";

export function LegalDocView({ doc }: { doc: LegalDocument }) {
  const { t } = useI18n();
  return (
    <main className="anim-in mx-auto max-w-2xl">
      <nav className="mb-4 text-sm anon-muted">
        <Link href="/" className="hover:text-white">
          ← {t("legal.back")}
        </Link>
        <span aria-hidden> / </span>
        <span>{doc.title}</span>
      </nav>
      <article className="anon-card p-6 sm:p-8">
        <h1 className="text-3xl font-semibold">{doc.title}</h1>
        {doc.subtitle && <p className="mt-2 text-sm anon-muted">{doc.subtitle}</p>}
        {!doc.publishable && (
          <p className="mt-4 rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-sm text-amber-100">
            {t("legal.pending")}
          </p>
        )}
        <div className="mt-8 space-y-8">
          {doc.sections.map((s) => (
            <section key={s.heading}>
              <h2 className="text-lg font-semibold">{s.heading}</h2>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-white/85">
                {s.body}
              </p>
            </section>
          ))}
        </div>
      </article>
    </main>
  );
}
