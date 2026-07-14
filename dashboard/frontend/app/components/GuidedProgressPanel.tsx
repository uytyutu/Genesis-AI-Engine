"use client";

import { useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  GUIDED_COMMERCE_EVENT,
  GUIDED_PREVIEW_STEPS,
  guidedPreviewPercent,
  loadGuidedCommerce,
  previewStepStatus,
  type GuidedCommerceState,
} from "../lib/guidedCommerce";
import { Card } from "./ui";
import { GuidedFactoryProductPreview } from "./GuidedFactoryProductPreview";
import { GuidedProvenancePanel, GuidedTrustPromise } from "./GuidedProvenancePanel";
import { getIndustryProfile } from "../lib/guidedOwnership";

type Props = {
  compact?: boolean;
  productLoading?: boolean;
  productError?: string;
};

export function GuidedProgressPanel({ compact, productLoading: productLoadingProp, productError: productErrorProp }: Props) {
  const [state, setState] = useState<GuidedCommerceState>(() => loadGuidedCommerce());
  const [productLoading, setProductLoading] = useState(false);
  const [productError, setProductError] = useState("");

  useEffect(() => {
    const sync = (e: Event) => {
      const detail = (e as CustomEvent<GuidedCommerceState>).detail;
      if (detail) setState(detail);
      else setState(loadGuidedCommerce());
    };
    const syncProduct = (e: Event) => {
      const detail = (e as CustomEvent<{ loading?: boolean; error?: string }>).detail;
      if (!detail) return;
      if (detail.loading != null) setProductLoading(detail.loading);
      if (detail.error != null) setProductError(detail.error);
    };
    window.addEventListener(GUIDED_COMMERCE_EVENT, sync);
    window.addEventListener("genesis:guided-product-status", syncProduct);
    return () => {
      window.removeEventListener(GUIDED_COMMERCE_EVENT, sync);
      window.removeEventListener("genesis:guided-product-status", syncProduct);
    };
  }, []);

  const percent = guidedPreviewPercent(state);
  const barWidth = Math.max(state.goalId ? 10 : 4, percent);
  const name = state.companyName.trim();
  const showPreview = Boolean(state.goalId);
  const industry = getIndustryProfile(state.goalId);
  const previewLoading = productLoadingProp ?? productLoading;
  const previewError = productErrorProp ?? productError;

  const previewCaption = !state.goalId
    ? "Черновик появится здесь"
    : state.productId
      ? name
        ? `Черновик сайта — ${name}`
        : "Черновик вашего сайта"
      : name
        ? `Собираем сайт для ${name}`
        : industry.categoryLabel;

  return (
    <Card
      glow={Boolean(state.goalId)}
      padding={compact ? "md" : "lg"}
      hover={false}
      className={`flex h-full min-h-0 flex-col ${
        state.goalId ? "border-genesis-accent/20" : "border-dashed border-white/12 bg-genesis-panel/40"
      }`}
    >
      <p className="text-[10px] font-bold tracking-[0.2em] text-genesis-accent uppercase">
        {name ? "Ваш бизнес" : "Предпросмотр"}
      </p>
      <h2 className="mt-2 text-lg font-bold text-white sm:text-xl">
        {name || previewCaption}
      </h2>
      {name ? (
        <p className="mt-1 text-xs text-genesis-muted">{previewCaption}</p>
      ) : null}

      {name ? (
        <GuidedTrustPromise className="mt-3" />
      ) : null}

      <div className="mt-3">
        <div className="mb-1 flex justify-between text-xs">
          <span className="text-genesis-muted">Сборка</span>
          <span className="font-semibold text-genesis-accent">{percent}%</span>
        </div>
        <div className="font-mono text-[10px] tracking-widest text-genesis-muted/80">
          {"□".repeat(Math.max(0, 10 - Math.round(percent / 10)))}
          <span className="text-genesis-accent">{"■".repeat(Math.round(percent / 10))}</span>
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-genesis-accent to-emerald-500 transition-all duration-500"
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {showPreview ? (
        <>
          <GuidedFactoryProductPreview
            state={state}
            loading={previewLoading}
            error={previewError}
          />
          <GuidedProvenancePanel state={state} compact={compact} />
        </>
      ) : (
        <div className="mt-4 flex min-h-[10rem] items-center justify-center rounded-xl border border-dashed border-white/12 bg-white/[0.02] px-4 text-center text-sm text-genesis-muted">
          Название компании — в блоке ниже. {ASSISTANT_NAME} соберёт черновик здесь.
        </div>
      )}

      <ul className="mt-4 min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
        {GUIDED_PREVIEW_STEPS.map((step) => {
          const status = previewStepStatus(step.id, state);
          return (
            <li
              key={step.id}
              className="flex items-center gap-2 rounded-lg bg-white/5 px-2.5 py-1.5 text-sm"
            >
              <span
                className={
                  status === "done"
                    ? "text-emerald-300"
                    : status === "active"
                      ? "font-medium text-genesis-accent"
                      : "text-genesis-muted"
                }
              >
                {status === "done" ? "✓" : status === "active" ? "⏳" : "○"} {step.label}
              </span>
            </li>
          );
        })}
      </ul>

      <p className="mt-3 text-xs text-genesis-muted">
        {state.step === "pay"
          ? "Последний шаг — оплата. Сайт справа остаётся вашим."
          : state.step === "offer"
            ? "Решение о покупке — здесь, без каталога и переходов."
            : state.step === "draft_ready"
              ? "Проверьте справа: каждый элемент — из вашего ответа. После оплаты — именно он."
              : state.goalId
                  ? `${ASSISTANT_NAME} собирает ваш сайт — вы видите это в реальном времени.`
                  : `Расскажите о бизнесе слева — ${ASSISTANT_NAME} начнёт работу.`}
      </p>
    </Card>
  );
}
