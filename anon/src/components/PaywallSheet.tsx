"use client";

import Link from "next/link";
import { useI18n } from "./I18nProvider";

export function PaywallSheet({
  open,
  onClose,
  titleKey,
  bodyKey,
  packHref = "/plus",
  packLabelKey = "cta.viewPlus",
  youGetKeys,
  forWhomKey,
  priceLabel,
}: {
  open: boolean;
  onClose: () => void;
  titleKey: string;
  bodyKey: string;
  packHref?: string;
  packLabelKey?: string;
  youGetKeys?: string[];
  forWhomKey?: string;
  priceLabel?: string;
}) {
  const { t } = useI18n();
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center">
      <div
        className="anon-card anim-in w-full max-w-md space-y-4 p-6"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs tracking-[0.3em] text-violet-300">✨ ANON</p>
            <h2 className="mt-2 text-xl font-semibold">{t(titleKey)}</h2>
          </div>
          {priceLabel ? (
            <span className="rounded-full bg-violet-500/20 px-3 py-1 text-xs font-semibold text-violet-100">
              {priceLabel}
            </span>
          ) : null}
        </div>
        <p className="text-sm anon-muted">{t(bodyKey)}</p>
        {youGetKeys && youGetKeys.length > 0 && (
          <div className="rounded-2xl bg-black/30 p-3 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
              {t("offer.youGet")}
            </p>
            <ul className="mt-2 space-y-1 anon-muted">
              {youGetKeys.map((k) => (
                <li key={k}>• {t(k)}</li>
              ))}
            </ul>
          </div>
        )}
        {forWhomKey ? (
          <p className="text-xs">
            <span className="anon-muted">{t("offer.forWhom")} </span>
            {t(forWhomKey)}
          </p>
        ) : null}
        <p className="text-xs anon-muted">{t("offer.afterPay")}</p>
        <div className="flex flex-col gap-2">
          <Link href={packHref} className="anon-btn anon-btn-primary w-full">
            {t(packLabelKey)}
          </Link>
          <button type="button" className="anon-btn anon-btn-ghost w-full" onClick={onClose}>
            {t("cta.close")}
          </button>
        </div>
      </div>
    </div>
  );
}
