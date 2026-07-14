"use client";

import { useCallback, useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  GUIDED_COMMERCE_EVENT,
  GUIDED_SITE_INCLUDES,
  advanceGuidedToOffer,
  advanceGuidedToPay,
  loadGuidedCommerce,
  markGuidedProductOwned,
  saveGuidedCommerce,
  setGuidedClientEmail,
  setGuidedLogoChoice,
  setGuidedProductId,
  submitCompanyNameAndAdvance,
  type GuidedCommerceState,
  type LogoChoice,
} from "../lib/guidedCommerce";
import { createGuidedSiteOrder, fetchGuidedBasicPackage } from "../lib/guidedOrder";
import { ensureGuidedDraftProduct } from "../lib/guidedProduct";
import { fetchPaymentInfo, startOrderCheckout } from "../lib/orderCheckout";
import { formatLocalizedMoney } from "../lib/formatEur";
import { getVisitorId } from "../lib/visitorId";
import { publicApiBase } from "../lib/publicApiBase";
import { SpringPressable } from "./motion/SpringPressable";

const API = publicApiBase();

export function VectorCommerceSteps() {
  const [state, setState] = useState<GuidedCommerceState>(() => loadGuidedCommerce());
  const [companyInput, setCompanyInput] = useState(() => loadGuidedCommerce().companyName);
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
    if (base.productId) return base;
    setProductBusy(true);
    setProductError("");
    try {
      const productId = await ensureGuidedDraftProduct(base);
      return setGuidedProductId(productId);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось собрать черновик";
      setProductError(message);
      throw e;
    } finally {
      setProductBusy(false);
    }
  }, []);

  const submitCompany = useCallback(async () => {
    const next = submitCompanyNameAndAdvance(companyInput);
    setState(next);
    try {
      const withProduct = await buildDraftProduct(next);
      setState(withProduct);
    } catch {
      /* surfaced in preview */
    }
  }, [companyInput, buildDraftProduct]);

  const pickLogo = useCallback((choice: LogoChoice) => {
    setState(setGuidedLogoChoice(choice));
  }, []);

  const continueToOffer = useCallback(async () => {
    if (!state.productId) {
      setFlowError("Дождитесь черновика справа — затем можно оформить");
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
  }, [state.productId]);

  const buySite = useCallback(async () => {
    const email = state.clientEmail.trim();
    if (!email) {
      setFlowError("Укажите email для подтверждения и чека");
      return;
    }
    if (!state.productId || !state.logoChoice) return;
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

  const priceDisplay =
    state.priceLabel ?? formatLocalizedMoney(state.priceEur ?? 399, "EUR");

  if (!state.goalId) return null;

  return (
    <div className="mt-3 shrink-0 space-y-3 border-t border-white/8 pt-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-genesis-accent">
        {ASSISTANT_NAME} — следующий шаг
      </p>

      {state.step === "company" ? (
        <div className="space-y-2">
          <p className="text-xs text-genesis-muted">
            Как называется ваша компания? {ASSISTANT_NAME} соберёт черновик сайта.
          </p>
          <input
            type="text"
            value={companyInput}
            onChange={(e) => setCompanyInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && companyInput.trim()) void submitCompany();
            }}
            placeholder="Например: Dr. Weber Zahnarzt"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none ring-genesis-accent/40 placeholder:text-genesis-muted/60 focus:border-genesis-accent/50 focus:ring-2"
          />
          <SpringPressable
            type="button"
            disabled={!companyInput.trim() || productBusy}
            onClick={() => void submitCompany()}
            className="w-full rounded-xl bg-genesis-accent py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {productBusy ? "Собираю черновик…" : "Показать черновик"}
          </SpringPressable>
        </div>
      ) : null}

      {state.step === "logo" && state.companyName.trim() ? (
        <div className="space-y-2">
          <p className="text-xs text-genesis-muted">Есть логотип?</p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                { id: "yes" as const, label: "Да" },
                { id: "no" as const, label: "Нет" },
                { id: "auto" as const, label: "Создать" },
              ] as const
            ).map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => pickLogo(opt.id)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${
                  state.logoChoice === opt.id
                    ? "border-genesis-accent/50 bg-genesis-accent/15 text-white"
                    : "border-white/10 text-genesis-muted"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {state.step === "draft_ready" && state.logoChoice ? (
        <SpringPressable
          type="button"
          disabled={flowBusy || !state.productId}
          onClick={() => void continueToOffer()}
          className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {flowBusy ? "Загружаем…" : "Оформить права на черновик"}
        </SpringPressable>
      ) : null}

      {state.step === "offer" ? (
        <div className="space-y-2">
          <p className="text-lg font-bold text-white">{priceDisplay}</p>
          <input
            type="email"
            value={state.clientEmail}
            onChange={(e) => setState(setGuidedClientEmail(e.target.value))}
            placeholder="Email"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white"
          />
          <SpringPressable
            type="button"
            disabled={flowBusy}
            onClick={() => void buySite()}
            className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {flowBusy ? "Оформляем…" : "Перейти к оплате"}
          </SpringPressable>
          <ul className="text-[10px] text-genesis-muted">
            {GUIDED_SITE_INCLUDES.slice(0, 4).map((item) => (
              <li key={item}>✓ {item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {state.step === "pay" && state.orderId ? (
        <div className="space-y-2">
          <p className="text-xs text-genesis-muted">
            Заказ {state.orderId} — оплата передаёт вам права на черновик справа.
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
            <p className="text-xs text-amber-100">Оплата скоро. Мы свяжемся на {state.clientEmail}.</p>
          )}
        </div>
      ) : null}

      {flowError ? (
        <p className="text-xs text-rose-300" role="alert">
          {flowError}
        </p>
      ) : null}
    </div>
  );
}
