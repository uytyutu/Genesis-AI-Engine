"use client";

import Link from "next/link";
import { PublicPageShell } from "./PublicPageShell";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * Shared storefront look for purchase / intake forms (AI Store, services, bots, Path A).
 * No Vector chat chrome — focused decision flow.
 */
export function OrderFormShell({
  children,
  backHref = "/site",
  backLabel,
  eyebrow,
  title,
  subtitle,
  priceLabel,
}: {
  children: React.ReactNode;
  backHref?: string;
  backLabel?: string;
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  priceLabel?: string;
}) {
  return (
    <PublicPageShell customerDecisionFlow minimal>
      <div className="mx-auto max-w-2xl space-y-6 pb-16 pt-2">
        <Link
          href={backHref}
          className="inline-flex text-sm font-medium text-emerald-300/90 hover:text-emerald-200 hover:underline"
        >
          {backLabel || `← ${BRAND_NAME}`}
        </Link>
        {(eyebrow || title) && (
          <header className="space-y-2">
            {eyebrow ? (
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-emerald-200/75">
                {eyebrow}
              </p>
            ) : null}
            {title ? (
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-[2rem]">
                {title}
              </h1>
            ) : null}
            {priceLabel ? (
              <p className="text-lg font-medium text-emerald-200/90">{priceLabel}</p>
            ) : null}
            {subtitle ? (
              <p className="max-w-xl text-sm leading-relaxed text-zinc-400">{subtitle}</p>
            ) : null}
          </header>
        )}
        <div className="rounded-[1.75rem] border border-white/10 bg-gradient-to-br from-white/[0.06] via-white/[0.03] to-transparent p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] sm:p-7">
          {children}
        </div>
      </div>
    </PublicPageShell>
  );
}
