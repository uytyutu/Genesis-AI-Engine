"use client";

import Link from "next/link";
import { useI18n } from "./I18nProvider";

/** Monetization clarity: what → for whom → after → price → action verb. */
export function ProductOfferCard({
  emoji,
  titleKey,
  blurbKey,
  youGetKeys,
  forWhomKey,
  recipientKeys,
  priceLabel,
  ctaHref,
  ctaKey,
  ctaVars,
  free,
}: {
  emoji: string;
  titleKey: string;
  blurbKey: string;
  youGetKeys: string[];
  forWhomKey: string;
  recipientKeys?: string[];
  priceLabel: string;
  ctaHref: string;
  ctaKey: string;
  ctaVars?: Record<string, string | number>;
  free?: boolean;
}) {
  const { t } = useI18n();

  return (
    <article className="anon-card flex flex-col p-5 transition hover:border-white/20">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-2xl">{emoji}</p>
          <h3 className="mt-2 text-lg font-semibold">{t(titleKey)}</h3>
          <p className="mt-1 text-sm anon-muted">{t(blurbKey)}</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
            free ? "bg-emerald-500/15 text-emerald-200" : "bg-violet-500/20 text-violet-100"
          }`}
        >
          {priceLabel}
        </span>
      </div>

      <div className="mt-4 space-y-3 text-sm">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300/90">
            {t("offer.youGet")}
          </p>
          <ul className="mt-2 space-y-1.5 anon-muted">
            {youGetKeys.map((k) => (
              <li key={k}>• {t(k)}</li>
            ))}
          </ul>
        </div>
        <p className="text-xs">
          <span className="anon-muted">{t("offer.forWhom")} </span>
          <span className="text-white/90">{t(forWhomKey)}</span>
        </p>
        {recipientKeys && recipientKeys.length > 0 && (
          <div className="rounded-2xl bg-black/30 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-fuchsia-300/90">
              {t("offer.recipientGets")}
            </p>
            <ul className="mt-2 space-y-1.5 text-xs anon-muted">
              {recipientKeys.map((k) => (
                <li key={k}>{t(k)}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <Link href={ctaHref} className="anon-btn anon-btn-primary mt-5 w-full">
        {t(ctaKey, ctaVars)}
      </Link>
    </article>
  );
}
