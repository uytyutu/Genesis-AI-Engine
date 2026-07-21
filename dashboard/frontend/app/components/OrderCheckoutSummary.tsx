"use client";

/**
 * A1.4 — Premium Checkout Experience (summary + trust + pay CTA).
 * No upsells, timers, or scarcity — calm confirmation before Stripe.
 */

import { useTranslation } from "react-i18next";
import { languageLabel } from "../lib/orderLiveGuidance";
import { uiLangForMarket } from "../lib/marketLang";
import { Badge, Button, Card } from "./ui";
import { OrderTrustCard } from "./OrderTrustCard";

export type CheckoutSummaryProps = {
  orderId: string;
  message: string;
  businessName: string;
  niche: string;
  marketCode: string;
  packageName: string;
  packageId: string;
  priceLabel: string;
  deliverables: string[];
  purchaseType: "one_time" | "subscription";
  paymentReady: boolean;
  confirmed: boolean;
  onConfirmedChange: (v: boolean) => void;
  payBusy: boolean;
  payError: string;
  onPay: () => void;
  launch?: boolean;
};

export function OrderCheckoutSummary({
  orderId,
  message,
  businessName,
  niche,
  marketCode,
  packageName,
  packageId,
  priceLabel,
  deliverables,
  purchaseType,
  paymentReady,
  confirmed,
  onConfirmedChange,
  payBusy,
  payError,
  onPay,
  launch = false,
}: CheckoutSummaryProps) {
  const { t } = useTranslation("site");
  const market = (marketCode || "DE").toUpperCase();
  const lang = uiLangForMarket(market);
  const nicheLabel = t(`order.liveNiche.${niche || "generic"}`, {
    defaultValue: niche || "generic",
  });

  const afterPay = [
    t("order.checkoutAfterRegistered"),
    t("order.checkoutAfterFactory"),
    t("order.checkoutAfterCompliance"),
    t("order.checkoutAfterZip"),
    t("order.checkoutAfterEmail"),
  ];

  return (
    <div className="mx-auto max-w-lg space-y-5">
      <div className="text-center">
        <p className="text-4xl text-emerald-400" aria-hidden>
          ✓
        </p>
        <h1 className="mt-3 text-2xl font-bold">
          {launch ? t("order.projectLocked") : t("order.checkoutReadyTitle")}
        </h1>
        <p className="mt-2 text-sm text-genesis-muted">{message}</p>
        <Badge variant="muted" className="mt-3">
          № {orderId}
        </Badge>
      </div>

      <Card hover={false} padding="md" className="text-left">
        <p className="genesis-label">{t("order.checkoutSummaryTitle")}</p>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between gap-3">
            <dt className="text-genesis-muted">{t("order.checkoutCompany")}</dt>
            <dd className="text-right font-medium text-white">{businessName || "—"}</dd>
          </div>
          {!launch ? (
            <div className="flex justify-between gap-3">
              <dt className="text-genesis-muted">{t("order.liveAiNiche")}</dt>
              <dd className="text-right text-white/90">{nicheLabel}</dd>
            </div>
          ) : null}
          <div className="flex justify-between gap-3">
            <dt className="text-genesis-muted">{t("order.liveAiMarket")}</dt>
            <dd className="text-right text-white/90">{market}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-genesis-muted">{t("order.liveAiLang")}</dt>
            <dd className="text-right text-white/90">{languageLabel(lang)}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-genesis-muted">{t("order.checkoutPackage")}</dt>
            <dd className="text-right font-medium text-white">
              {packageName}
              <span className="ml-1 text-xs font-normal text-genesis-muted">({packageId})</span>
            </dd>
          </div>
        </dl>

        {deliverables.length > 0 ? (
          <>
            <p className="genesis-label mt-4">{t("order.youReceive")}</p>
            <ul className="mt-2 space-y-1.5 text-sm">
              {deliverables.map((d) => (
                <li key={d} className="flex gap-2">
                  <span className="text-emerald-400">✔</span>
                  <span>{d}</span>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </Card>

      <Card hover={false} padding="md" className="text-left">
        <p className="genesis-label">{t("order.checkoutAfterTitle")}</p>
        <ul className="mt-2 space-y-1.5 text-sm">
          {afterPay.map((line) => (
            <li key={line} className="flex gap-2">
              <span className="text-emerald-400">✓</span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Dominant pay block */}
      <Card glow padding="lg" className="text-center">
        <p className="text-sm text-genesis-muted">{packageName}</p>
        <p className="mt-1 text-3xl font-bold tabular-nums text-white sm:text-4xl">{priceLabel}</p>

        <label className="mt-5 flex cursor-pointer items-start gap-2.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-left text-sm">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => onConfirmedChange(e.target.checked)}
            className="mt-0.5 accent-emerald-500"
          />
          <span>{t("order.checkoutConfirmLabel")}</span>
        </label>

        {paymentReady ? (
          <div className="mt-4 space-y-3">
            <OrderTrustCard purchaseType={purchaseType} />
            <Button
              variant="success"
              size="lg"
              fullWidth
              loading={payBusy}
              disabled={!confirmed || payBusy}
              onClick={onPay}
            >
              {payBusy ? t("order.payBusy") : t("order.checkoutPayCta", { price: priceLabel })}
            </Button>
            {payError ? (
              <p className="text-xs text-rose-300" role="alert">
                {payError}
              </p>
            ) : null}
            {!confirmed ? (
              <p className="text-[11px] text-genesis-muted">{t("order.checkoutConfirmHint")}</p>
            ) : null}
          </div>
        ) : (
          <p className="mt-4 text-sm text-amber-200/90">{t("order.payUnavailable")}</p>
        )}
      </Card>
    </div>
  );
}
