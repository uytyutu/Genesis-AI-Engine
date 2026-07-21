"use client";

/**
 * A1.3 — Live order preview + Composer-rule guidance (no Factory ZIP).
 */

import { useTranslation } from "react-i18next";
import {
  buildOrderLiveGuidance,
  languageLabel,
  progressBars,
  type OrderLiveInput,
} from "../lib/orderLiveGuidance";

type Props = {
  input: OrderLiveInput;
  className?: string;
};

export function OrderLivePreviewPanel({ input, className = "" }: Props) {
  const { t } = useTranslation("site");
  const g = buildOrderLiveGuidance(input);
  const { palette } = g;
  const initials =
    g.previewTitle
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase() || "")
      .join("") || "VC";

  const nicheLabel = t(`order.liveNiche.${g.nicheId}`, {
    defaultValue: g.nicheId,
  });
  const styleLabel = t(`order.brandStyles.${g.styleId}.label`, {
    defaultValue: g.styleId,
  });

  return (
    <div className={`mt-4 space-y-3 ${className}`}>
      <div>
        <p className="text-xs font-medium text-white/90">{t("order.livePreviewTitle")}</p>
        <p className="mt-0.5 text-[11px] leading-snug text-genesis-muted">
          {t("order.livePreviewHint")}
        </p>
      </div>

      {/* Mini site chrome — reacts to name / niche / style / package */}
      <div
        className="overflow-hidden rounded-xl border border-white/10 shadow-lg"
        style={{ background: palette.surface, color: palette.ink }}
      >
        <div
          className="relative px-3 pb-4 pt-3"
          style={{ background: palette.gradient, minHeight: 132 }}
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[10px] font-bold text-white"
                style={{ background: "rgba(255,255,255,0.18)" }}
                aria-hidden
              >
                {initials}
              </span>
              <span className="truncate text-xs font-semibold text-white/95">
                {g.previewTitle}
              </span>
            </div>
            <span className="shrink-0 rounded-full bg-white/15 px-2 py-0.5 text-[9px] uppercase tracking-wide text-white/90">
              {g.packageId}
            </span>
          </div>
          <p className="mt-3 text-sm font-semibold leading-snug text-white">
            {g.previewTitle}
          </p>
          <p className="mt-1 line-clamp-2 text-[11px] text-white/75">{g.previewTagline}</p>
          <button
            type="button"
            tabIndex={-1}
            className="mt-3 rounded-full px-3 py-1 text-[10px] font-bold text-white"
            style={{ background: palette.accent, color: palette.primaryDark }}
            aria-hidden
          >
            {t("order.livePreviewCta")}
          </button>
        </div>
        <div className="grid grid-cols-3 gap-1.5 border-t border-black/5 bg-white/80 px-2 py-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-8 rounded-md"
              style={{ background: `${palette.primary}${i === 1 ? "33" : "18"}` }}
            />
          ))}
        </div>
      </div>

      {/* AI guidance — Composer rules, not LLM */}
      <div className="rounded-xl border border-emerald-500/25 bg-emerald-950/35 px-3 py-2.5">
        <p className="text-[11px] font-medium text-emerald-100">{t("order.liveAiTitle")}</p>
        <dl className="mt-2 space-y-1 text-[11px]">
          <div className="flex justify-between gap-2">
            <dt className="text-genesis-muted">{t("order.liveAiNiche")}</dt>
            <dd className="text-right text-white/90">{nicheLabel}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-genesis-muted">{t("order.liveAiStyle")}</dt>
            <dd className="text-right text-white/90">{styleLabel}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-genesis-muted">{t("order.liveAiHero")}</dt>
            <dd className="text-right text-white/90">
              {g.heroHint} ({g.heroLayout})
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-genesis-muted">{t("order.liveAiMarket")}</dt>
            <dd className="text-right text-white/90">{g.marketCode}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-genesis-muted">{t("order.liveAiLang")}</dt>
            <dd className="text-right text-white/90">{languageLabel(g.languageCode)}</dd>
          </div>
        </dl>
      </div>

      {/* Creation progress */}
      <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
        <p className="font-mono text-xs tracking-widest text-emerald-200/90" aria-hidden>
          {progressBars(g.progressFilled, g.progressTotal)}
        </p>
        <p className="mt-1 text-[11px] text-genesis-muted">
          {t("order.liveProgressLabel", {
            filled: g.progressFilled,
            total: g.progressTotal,
          })}
        </p>
        {g.readyIds.length > 0 ? (
          <ul className="mt-2 space-y-0.5 text-[11px] text-emerald-100/90">
            {g.readyIds.map((id) => (
              <li key={id} className="flex gap-1.5">
                <span aria-hidden>✔</span>
                <span>{t(`order.liveReady.${id}`)}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {g.remainingIds.length > 0 ? (
          <div className="mt-2">
            <p className="text-[10px] uppercase tracking-wide text-genesis-muted">
              {t("order.liveRemainingTitle")}
            </p>
            <ul className="mt-1 space-y-0.5 text-[11px] text-genesis-muted">
              {g.remainingIds.map((id) => (
                <li key={id}>○ {t(`order.liveReady.${id}`)}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-2 text-[11px] text-emerald-200">{t("order.liveAlmostReady")}</p>
        )}
      </div>
    </div>
  );
}
