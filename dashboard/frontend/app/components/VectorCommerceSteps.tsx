"use client";

import { useCallback, useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  GUIDED_COMMERCE_EVENT,
  GUIDED_SITE_INCLUDES,
  advanceGuidedToOffer,
  advanceGuidedToPay,
  confirmGuidedDraftReview,
  loadGuidedCommerce,
  markGuidedProductOwned,
  saveGuidedCommerce,
  setGuidedProductId,
  type GuidedCommerceState,
} from "../lib/guidedCommerce";
import {
  dialogGaps,
  isDialogReadyForDraft,
  pickDialogFollowUp,
  resolveDialogStep,
} from "../lib/guidedDialogEngine";
import { buildGuidedSalesBrief, guidedReviewSummary } from "../lib/guidedJourney";
import { createGuidedSiteOrder, fetchGuidedBasicPackage } from "../lib/guidedOrder";
import { ensureGuidedDraftProduct } from "../lib/guidedProduct";
import { fetchPaymentInfo, startOrderCheckout } from "../lib/orderCheckout";
import { formatLocalizedMoney } from "../lib/formatEur";
import { getVisitorId } from "../lib/visitorId";
import { publicApiBase } from "../lib/publicApiBase";
import { SpringPressable } from "./motion/SpringPressable";

const API = publicApiBase();

const GAP_LABEL: Record<string, string> = {
  company: "название компании",
  activity: "чем занимаетесь",
  vision: "цель сайта",
  audience: "аудитория",
  email: "email",
  logo: "логотип",
};

export function VectorCommerceSteps() {
  const [state, setState] = useState<GuidedCommerceState>(() => loadGuidedCommerce());
  const [flowBusy, setFlowBusy] = useState(false);
  const [flowError, setFlowError] = useState("");
  const [productBusy, setProductBusy] = useState(false);
  const [productError, setProductError] = useState("");
  const [paymentReady, setPaymentReady] = useState(false);
  const [isSandbox, setIsSandbox] = useState(false);

  useEffect(() => {
    const sync = (e: Event) => {
      const detail = (e as CustomEvent<GuidedCommerceState>).detail;
      if (detail) setState(detail);
      else setState(loadGuidedCommerce());
    };
    window.addEventListener(GUIDED_COMMERCE_EVENT, sync);
    return () => window.removeEventListener(GUIDED_COMMERCE_EVENT, sync);
  }, []);

  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent("genesis:guided-product-status", {
        detail: { loading: productBusy, error: productError },
      }),
    );
  }, [productBusy, productError]);

  useEffect(() => {
    fetchPaymentInfo().then((info) => {
      setPaymentReady(info.configured);
      setIsSandbox(info.sandbox);
    });
  }, []);

  const buildDraftProduct = useCallback(async (base: GuidedCommerceState) => {
    if (base.productId || !isDialogReadyForDraft(base)) return base;
    setProductBusy(true);
    setProductError("");
    try {
      const productId = await ensureGuidedDraftProduct(base);
      const withProduct = setGuidedProductId(productId);
      const next = { ...withProduct, step: resolveDialogStep(withProduct) };
      saveGuidedCommerce(next);
      setState(next);
      return next;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось собрать черновик";
      setProductError(message);
      throw e;
    } finally {
      setProductBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!isDialogReadyForDraft(state) || state.productId || productBusy) return;
    void buildDraftProduct(state);
  }, [state, productBusy, buildDraftProduct]);

  const continueToOffer = useCallback(async () => {
    if (!state.productId) {
      setFlowError("Черновик ещё собирается из вашего разговора");
      return;
    }
    if (!state.draftReviewed) {
      setFlowError("Сначала подтвердите, что черновик справа вас устраивает");
      return;
    }
    setFlowBusy(true);
    setFlowError("");
    try {
      const pkg = await fetchGuidedBasicPackage();
      setState(advanceGuidedToOffer(pkg?.price_eur ?? 399, pkg?.price_label ?? null));
    } catch {
      setState(advanceGuidedToOffer(399, null));
    } finally {
      setFlowBusy(false);
    }
  }, [state.productId, state.draftReviewed]);

  const approveDraft = useCallback(() => {
    const next = confirmGuidedDraftReview();
    setState(next);
    void continueToOffer();
  }, [continueToOffer]);

  const buySite = useCallback(async () => {
    const email = state.clientEmail.trim();
    if (!email) return;
    if (!state.productId || !state.logoChoice || !state.draftReviewed) return;
    setFlowBusy(true);
    setFlowError("");
    try {
      const order = await createGuidedSiteOrder({
        businessName: state.companyName.trim(),
        email,
        visitorId: getVisitorId("public"),
        goalLabel: "Получить сайт",
        logoChoice: state.logoChoice,
        productId: state.productId,
        description: buildGuidedSalesBrief(state),
        city: state.clientCity,
        phone: state.clientPhone,
        extraWishes: state.siteVision,
      });
      setState(
        advanceGuidedToPay(order.orderId, order.priceEur, order.priceLabel ?? state.priceLabel),
      );
    } catch (e) {
      setFlowError(e instanceof Error ? e.message : "Не удалось оформить заказ");
    } finally {
      setFlowBusy(false);
    }
  }, [state]);

  const pay = useCallback(async () => {
    if (!state.orderId) return;
    setFlowBusy(true);
    setFlowError("");
    try {
      if (isSandbox) {
        const res = await fetch(`${API}/api/sales/orders/${state.orderId}/pay-sandbox`, {
          method: "POST",
        });
        const body = await res.json();
        if (!res.ok) {
          setFlowError(typeof body.detail === "string" ? body.detail : "Оплата не прошла");
          return;
        }
        markGuidedProductOwned();
        window.location.href = `/order/status/${state.orderId}?paid=1`;
        return;
      }
      const url = await startOrderCheckout(state.orderId);
      window.location.href = url;
    } catch (e) {
      setFlowError(e instanceof Error ? e.message : "Не удалось начать оплату");
    } finally {
      setFlowBusy(false);
    }
  }, [state.orderId, isSandbox]);

  const priceDisplay = state.priceLabel ?? formatLocalizedMoney(state.priceEur ?? 399, "EUR");

  if (!state.goalId) return null;

  const known = guidedReviewSummary(state);
  const gaps = dialogGaps(state);
  const followUp = pickDialogFollowUp(state);

  return (
    <div className="mt-3 shrink-0 space-y-3 border-t border-white/8 pt-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-genesis-accent">
        Ваш проект из диалога
      </p>

      {state.step === "discover" || state.step === "review" ? (
        <div className="space-y-2">
          {known.length ? (
            <ul className="space-y-1 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-[11px] text-genesis-muted">
              {known.map((line) => (
                <li key={line}>
                  <span className="text-emerald-300/90">✓</span> {line}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-genesis-muted">
              Напишите {ASSISTANT_NAME} слева — чем занимаетесь и какой сайт нужен. Без анкеты.
            </p>
          )}

          {gaps.length ? (
            <p className="text-[11px] leading-relaxed text-genesis-muted">
              {ASSISTANT_NAME} уточнит в чате
              {followUp ? `: «${followUp}»` : ` — не хватает: ${gaps.map((g) => GAP_LABEL[g] ?? g).join(", ")}`}
            </p>
          ) : productBusy ? (
            <p className="text-xs text-genesis-accent">Собираю черновик из разговора…</p>
          ) : null}
        </div>
      ) : null}

      {state.step === "review" && state.productId ? (
        <div className="space-y-2">
          <p className="text-xs text-emerald-100/90">
            Сверьте черновик справа с тем, что вы рассказали. Не то — продолжайте диалог слева.
          </p>
          <SpringPressable
            type="button"
            disabled={flowBusy || productBusy}
            onClick={approveDraft}
            className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {flowBusy ? "Готовим оформление…" : "Черновик подходит — оформить права"}
          </SpringPressable>
        </div>
      ) : null}

      {state.step === "offer" ? (
        <div className="space-y-2">
          <p className="text-lg font-bold text-white">{priceDisplay}</p>
          <p className="text-xs text-genesis-muted">
            Права на согласованный черновик — тот же сайт, без пересборки.
          </p>
          <SpringPressable
            type="button"
            disabled={flowBusy}
            onClick={() => void buySite()}
            className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {flowBusy ? "Оформляем…" : "Перейти к оплате"}
          </SpringPressable>
          <ul className="text-[10px] text-genesis-muted">
            {GUIDED_SITE_INCLUDES.map((item) => (
              <li key={item}>✓ {item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {state.step === "pay" && state.orderId ? (
        <div className="space-y-2">
          <p className="text-xs text-genesis-muted">
            Заказ {state.orderId} — оплата закрепляет согласованный результат.
          </p>
          {paymentReady ? (
            <SpringPressable
              type="button"
              disabled={flowBusy}
              onClick={() => void pay()}
              className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white"
            >
              {flowBusy ? "Переход…" : `Оплатить ${priceDisplay}`}
            </SpringPressable>
          ) : (
            <p className="text-xs text-amber-100">Оплата скоро. Свяжемся на {state.clientEmail}.</p>
          )}
        </div>
      ) : null}

      {flowError ? (
        <p className="text-xs text-rose-300" role="alert">
          {flowError}
        </p>
      ) : null}
      {productError ? (
        <p className="text-xs text-rose-300" role="alert">
          {productError}
        </p>
      ) : null}
    </div>
  );
}
