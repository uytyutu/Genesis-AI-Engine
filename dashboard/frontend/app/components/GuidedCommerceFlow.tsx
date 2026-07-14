"use client";

import { useCallback, useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  GUIDED_GOALS,
  GUIDED_COMMERCE_EVENT,
  GUIDED_SITE_INCLUDES,
  advanceGuidedToOffer,
  advanceGuidedToPay,
  loadGuidedCommerce,
  markGuidedProductOwned,
  resetGuidedCommerce,
  saveGuidedCommerce,
  selectGuidedGoal,
  setGuidedClientEmail,
  setGuidedLogoChoice,
  setGuidedProductId,
  submitCompanyNameAndAdvance,
  type GuidedCommerceState,
  type GuidedGoalId,
  type LogoChoice,
} from "../lib/guidedCommerce";
import { createGuidedSiteOrder, fetchGuidedBasicPackage } from "../lib/guidedOrder";
import { ensureGuidedDraftProduct } from "../lib/guidedProduct";
import { buildGuidedSalesBrief } from "../lib/guidedJourney";
import { fetchPaymentInfo, startOrderCheckout } from "../lib/orderCheckout";
import { formatLocalizedMoney } from "../lib/formatEur";
import { getIndustryProfile } from "../lib/guidedOwnership";
import { getVisitorId } from "../lib/visitorId";
import { GuidedTrustPromise } from "./GuidedProvenancePanel";
import { publicApiBase } from "../lib/publicApiBase";
import { SpringIn } from "./motion/SpringIn";
import { SpringPressable } from "./motion/SpringPressable";
import { Card } from "./ui";

const API = publicApiBase();

type Props = {
  onNeedHelp: () => void;
};

function HelpLink({ onNeedHelp }: { onNeedHelp: () => void }) {
  return (
    <div className="mt-auto border-t border-white/8 pt-4">
      <button
        type="button"
        onClick={onNeedHelp}
        className="text-sm text-genesis-muted underline-offset-2 transition hover:text-white hover:underline"
      >
        Нужна помощь?
      </button>
    </div>
  );
}

export function GuidedCommerceFlow({ onNeedHelp }: Props) {
  const [state, setState] = useState<GuidedCommerceState>(() => loadGuidedCommerce());
  const [companyInput, setCompanyInput] = useState(() => loadGuidedCommerce().companyName);

  useEffect(() => {
    const sync = (e: Event) => {
      const detail = (e as CustomEvent<GuidedCommerceState>).detail;
      if (detail) setState(detail);
      else setState(loadGuidedCommerce());
    };
    window.addEventListener(GUIDED_COMMERCE_EVENT, sync);
    return () => window.removeEventListener(GUIDED_COMMERCE_EVENT, sync);
  }, []);

  const [flowBusy, setFlowBusy] = useState(false);
  const [flowError, setFlowError] = useState("");
  const [comingSoonNote, setComingSoonNote] = useState("");
  const [productBusy, setProductBusy] = useState(false);
  const [productError, setProductError] = useState("");

  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent("genesis:guided-product-status", {
        detail: { loading: productBusy, error: productError },
      }),
    );
  }, [productBusy, productError]);

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
      /* productError surfaced in preview panel */
    }
  }, [companyInput, buildDraftProduct]);

  const pickGoal = useCallback((goalId: GuidedGoalId) => {
    if (!GUIDED_GOALS.find((g) => g.id === goalId)?.available) {
      setComingSoonNote(
        "Этот сценарий ещё в разработке. Сейчас доступен путь «Получить сайт».",
      );
      return;
    }
    setComingSoonNote("");
    const next = selectGuidedGoal(goalId);
    setState(next);
    setCompanyInput("");
  }, []);

  const pickLogo = useCallback((choice: LogoChoice) => {
    const next = setGuidedLogoChoice(choice);
    setState(next);
  }, []);

  const continueToOffer = useCallback(async () => {
    if (!state.productId) {
      setFlowError("Дождитесь сборки черновика справа — затем можно оформить заказ");
      return;
    }
    setFlowBusy(true);
    setFlowError("");
    try {
      const pkg = await fetchGuidedBasicPackage();
      const price = pkg?.price_eur ?? 399;
      const label = pkg?.price_label ?? null;
      setState(advanceGuidedToOffer(price, label));
    } catch {
      setState(advanceGuidedToOffer(399, null));
    } finally {
      setFlowBusy(false);
    }
  }, [state.productId]);

  const buySite = useCallback(async () => {
    const email = state.clientEmail.trim();
    if (!email) {
      setFlowError("Укажите email — на него придёт подтверждение и чек");
      return;
    }
    if (!state.goalId || !state.logoChoice || !state.productId) {
      setFlowError("Сначала дождитесь черновика Product справа");
      return;
    }
    setFlowBusy(true);
    setFlowError("");
    try {
      const goalLabel = GUIDED_GOALS.find((g) => g.id === state.goalId)?.label ?? "";
      const order = await createGuidedSiteOrder({
        businessName: state.companyName.trim(),
        email,
        visitorId: getVisitorId("public"),
        goalLabel,
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

  const returnToOffer = useCallback(() => {
    void continueToOffer();
  }, [continueToOffer]);

  const goalLabel = GUIDED_GOALS.find((g) => g.id === state.goalId)?.label ?? "";
  const industry = getIndustryProfile(state.goalId);
  const priceDisplay =
    state.priceLabel ??
    formatLocalizedMoney(state.priceEur ?? 399, "EUR");

  if (state.step === "pay" && state.orderId) {
    return (
      <GuidedPayStep
        state={state}
        priceDisplay={priceDisplay}
        onNeedHelp={onNeedHelp}
        onBack={() => {
          const prev = loadGuidedCommerce();
          const next = { ...prev, step: "offer" as const };
          setState(next);
          saveGuidedCommerce(next);
        }}
      />
    );
  }

  if (state.step === "offer" && state.goalId && state.companyName.trim() && state.logoChoice) {
    return (
      <Card
        padding="lg"
        hover={false}
        className="flex h-full min-h-0 flex-col border-genesis-accent/25 bg-genesis-panel/60"
      >
        <SpringIn>
          <button
            type="button"
            onClick={() => {
              const prev = loadGuidedCommerce();
              const next = { ...prev, step: "draft_ready" as const };
              setState(next);
              saveGuidedCommerce(next);
            }}
            className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
          >
            ← Назад
          </button>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-genesis-accent">
            Оформление
          </p>
          <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">Ваш сайт готов</h2>
          <GuidedTrustPromise className="mt-3" />
          <p className="mt-2 text-sm text-genesis-muted">
            {state.companyName.trim()} — справа черновик вашего Product. После оплаты вы получаете
            права на тот же объект, без повторной сборки.
          </p>
        </SpringIn>

        <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-genesis-muted">
          Что входит
        </p>
        <ul className="mt-2 space-y-1.5 text-sm">
          {GUIDED_SITE_INCLUDES.map((item) => (
            <li key={item} className="flex gap-2 text-emerald-100">
              <span className="text-emerald-400">✓</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>

        <div className="mt-5 rounded-xl border border-white/10 bg-white/5 px-4 py-4">
          <p className="text-xs text-genesis-muted">Стоимость</p>
          <p className="mt-1 text-3xl font-bold tabular-nums text-white">{priceDisplay}</p>
          <p className="mt-1 text-xs text-genesis-muted">Фиксированная цена — без скрытых платежей</p>
        </div>

        <label className="mt-5 block text-sm font-medium text-genesis-muted" htmlFor="guided-email">
          Email для подтверждения
        </label>
        <input
          id="guided-email"
          type="email"
          value={state.clientEmail}
          onChange={(e) => {
            const next = setGuidedClientEmail(e.target.value);
            setState(next);
          }}
          placeholder="hello@…"
          className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-base text-white outline-none ring-genesis-accent/40 placeholder:text-genesis-muted/60 focus:border-genesis-accent/50 focus:ring-2"
        />

        {flowError ? (
          <p className="mt-2 text-xs text-rose-300" role="alert">
            {flowError}
          </p>
        ) : null}

        <div className="mt-5 flex flex-col gap-2">
          <SpringPressable
            type="button"
            disabled={flowBusy}
            onClick={buySite}
            className="w-full rounded-xl bg-emerald-600 py-3.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
          >
            {flowBusy ? "Оформляем…" : "Купить сайт"}
          </SpringPressable>
        </div>

        <HelpLink onNeedHelp={onNeedHelp} />
      </Card>
    );
  }

  if (state.step === "tune" && state.goalId && state.companyName.trim()) {
    return (
      <Card
        padding="lg"
        hover={false}
        className="flex h-full min-h-0 flex-col border-amber-500/15 bg-genesis-panel/60"
      >
        <SpringIn>
          <button
            type="button"
            onClick={() => {
              const prev = loadGuidedCommerce();
              const next = { ...prev, step: "offer" as const };
              setState(next);
              saveGuidedCommerce(next);
            }}
            className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
          >
            ← К оформлению
          </button>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-400">
            Настройка
          </p>
          <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">Почти готово к оплате</h2>
          <p className="mt-2 text-sm text-genesis-muted">
            Дополнительная настройка (галерея, контакты) появится позже. Сейчас можно перейти к
            оформлению — ваш черновик справа уже сохранён.
          </p>
        </SpringIn>

        <SpringPressable
          type="button"
          disabled={flowBusy}
          onClick={returnToOffer}
          className="mt-5 w-full rounded-xl bg-genesis-accent py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {flowBusy ? "Загружаем…" : "Перейти к оформлению и оплате"}
        </SpringPressable>

        <HelpLink onNeedHelp={onNeedHelp} />
      </Card>
    );
  }

  if (state.step === "draft_ready" && state.goalId && state.companyName.trim() && state.logoChoice) {
    return (
      <Card
        padding="lg"
        hover={false}
        className="flex h-full min-h-0 flex-col border-emerald-500/20 bg-genesis-panel/60"
      >
        <SpringIn>
          <button
            type="button"
            onClick={() => {
              const prev = loadGuidedCommerce();
              const next = { ...prev, step: "logo" as const };
              setState(next);
              saveGuidedCommerce(next);
            }}
            className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
          >
            ← Назад
          </button>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">
            {goalLabel}
          </p>
          <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">
            Черновик вашего Product готов
          </h2>
          <GuidedTrustPromise className="mt-3" />
          <p className="mt-3 text-sm text-genesis-muted">
            {state.companyName.trim()} — справа сайт, собранный Factory. Проверьте черновик и
            переходите к оформлению.
          </p>
        </SpringIn>

        <ul className="mt-5 space-y-3 text-sm">
          <li className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-4 py-3 text-emerald-100">
            <span className="mr-2">🟢</span>
            <strong className="font-medium text-white">Узнать стоимость и купить</strong>
            <span className="mt-1 block text-genesis-muted">
              Фиксированная цена — справа тот же Product, что вы покупаете
            </span>
          </li>
        </ul>

        {flowError ? (
          <p className="mt-3 text-xs text-rose-300" role="alert">
            {flowError}
          </p>
        ) : null}

        <div className="mt-5 flex flex-col gap-2">
          <SpringPressable
            type="button"
            disabled={flowBusy}
            onClick={() => void continueToOffer()}
            className="w-full rounded-xl bg-genesis-accent py-3.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {flowBusy ? "Загружаем…" : "Продолжить оформление"}
          </SpringPressable>
        </div>

        <HelpLink onNeedHelp={onNeedHelp} />
      </Card>
    );
  }

  if (state.step === "logo" && state.goalId && state.companyName.trim()) {
    return (
      <Card
        padding="lg"
        hover={false}
        className="flex h-full min-h-0 flex-col border-genesis-accent/15 bg-genesis-panel/60"
      >
        <SpringIn>
          <button
            type="button"
            onClick={() => {
              const prev = loadGuidedCommerce();
              const next = { ...prev, step: "company" as const, logoChoice: null };
              setState(next);
              saveGuidedCommerce(next);
            }}
            className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
          >
            ← Назад
          </button>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-genesis-accent">
            {goalLabel}
          </p>
          <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">У вас уже есть логотип?</h2>
          <p className="mt-2 text-sm text-genesis-muted">
            Справа — черновик вашего Product. Выберите вариант с логотипом.
          </p>
        </SpringIn>

        <ul className="mt-6 space-y-2">
          {(
            [
              { id: "yes" as const, label: "Да, есть логотип" },
              { id: "no" as const, label: "Нет" },
              { id: "auto" as const, label: "Создать автоматически" },
            ] as const
          ).map((opt, i) => (
            <SpringIn key={opt.id} delay={0.05 * i}>
              <li>
                <SpringPressable
                  type="button"
                  onClick={() => pickLogo(opt.id)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3.5 text-left text-sm font-medium transition sm:text-base ${
                    state.logoChoice === opt.id
                      ? "border-genesis-accent/50 bg-genesis-accent/15 text-white"
                      : "border-white/10 bg-white/5 text-white hover:border-genesis-accent/40 hover:bg-genesis-accent/10"
                  }`}
                >
                  <span className="text-lg">{state.logoChoice === opt.id ? "●" : "○"}</span>
                  {opt.label}
                </SpringPressable>
              </li>
            </SpringIn>
          ))}
        </ul>

        <HelpLink onNeedHelp={onNeedHelp} />
      </Card>
    );
  }

  if (state.step === "company" && state.goalId) {
    return (
      <Card
        padding="lg"
        hover={false}
        className="flex h-full min-h-0 flex-col border-genesis-accent/15 bg-genesis-panel/60"
      >
        <SpringIn>
          <button
            type="button"
            onClick={() => {
              const next = resetGuidedCommerce();
              setState(next);
              setCompanyInput("");
            }}
            className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
          >
            ← Другая цель
          </button>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-genesis-accent">
            {goalLabel}
          </p>
          <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">Как называется ваша компания?</h2>
          <p className="mt-2 text-sm text-genesis-muted">
            Один вопрос — и справа Factory соберёт черновик вашего сайта.
          </p>
        </SpringIn>

        <label className="mt-6 block text-sm font-medium text-genesis-muted" htmlFor="guided-company">
          Название компании
        </label>
        <input
          id="guided-company"
          type="text"
          value={companyInput}
          onChange={(e) => setCompanyInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && companyInput.trim()) submitCompany();
          }}
          placeholder="Например: BauTeam Schmidt"
          className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-base text-white outline-none ring-genesis-accent/40 placeholder:text-genesis-muted/60 focus:border-genesis-accent/50 focus:ring-2"
          autoFocus
        />
        <SpringPressable
          type="button"
          disabled={!companyInput.trim()}
          onClick={submitCompany}
          className="mt-4 w-full rounded-xl bg-genesis-accent py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-40 sm:w-auto sm:px-8"
        >
          Далее
        </SpringPressable>

        <HelpLink onNeedHelp={onNeedHelp} />
      </Card>
    );
  }

  return (
    <Card
      padding="lg"
      hover={false}
      className="flex h-full min-h-0 flex-col border-genesis-accent/15 bg-genesis-panel/60"
    >
      <SpringIn>
        <div className="mb-1 flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-genesis-accent to-indigo-600 text-sm font-bold text-white shadow-lg shadow-genesis-accent/25">
            V
          </span>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-genesis-accent">
            {ASSISTANT_NAME}
          </p>
        </div>
        <h2 className="mt-2 text-xl font-bold leading-snug text-white sm:text-2xl">Здравствуйте.</h2>
        <p className="mt-2 text-sm leading-relaxed text-genesis-muted sm:text-base">
          Сейчас доступен путь «Получить сайт». Остальные сценарии — в разработке.
        </p>
        <p className="mt-3 text-base font-semibold text-white">Что вы хотите получить сегодня?</p>
      </SpringIn>

      {comingSoonNote ? (
        <p className="mt-3 rounded-xl border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-xs text-amber-100/90">
          {comingSoonNote}
        </p>
      ) : null}

      <ul className="mt-4 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        {GUIDED_GOALS.map((goal, i) => (
          <SpringIn key={goal.id} delay={0.04 * i}>
            <li>
              <SpringPressable
                type="button"
                onClick={() => pickGoal(goal.id)}
                className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3.5 text-left text-sm font-medium transition sm:text-base ${
                  goal.available
                    ? "border-white/10 bg-white/5 text-white hover:border-genesis-accent/40 hover:bg-genesis-accent/10 hover:shadow-[0_0_24px_rgba(99,102,241,0.12)]"
                    : "border-white/6 bg-white/[0.02] text-genesis-muted hover:border-white/12"
                }`}
              >
                <span
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-xl ${
                    goal.available
                      ? "bg-gradient-to-br from-white/10 to-white/5"
                      : "bg-white/[0.04] opacity-60"
                  }`}
                >
                  {goal.emoji}
                </span>
                <span className="flex min-w-0 flex-1 items-center justify-between gap-2">
                  <span>{goal.label}</span>
                  {!goal.available ? (
                    <span className="shrink-0 rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-genesis-muted">
                      Скоро
                    </span>
                  ) : null}
                </span>
              </SpringPressable>
            </li>
          </SpringIn>
        ))}
      </ul>

      <HelpLink onNeedHelp={onNeedHelp} />
    </Card>
  );
}

function GuidedPayStep({
  state,
  priceDisplay,
  onNeedHelp,
  onBack,
}: {
  state: GuidedCommerceState;
  priceDisplay: string;
  onNeedHelp: () => void;
  onBack: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [isSandbox, setIsSandbox] = useState(false);
  const [paymentReady, setPaymentReady] = useState(false);

  useEffect(() => {
    fetchPaymentInfo().then((info) => {
      setIsSandbox(info.sandbox);
      setPaymentReady(info.configured);
    });
  }, []);

  async function pay() {
    if (!state.orderId) return;
    setBusy(true);
    setError("");
    try {
      if (isSandbox) {
        const res = await fetch(`${API}/api/sales/orders/${state.orderId}/pay-sandbox`, {
          method: "POST",
        });
        const body = await res.json();
        if (!res.ok) {
          setError(typeof body.detail === "string" ? body.detail : "Оплата не прошла");
          return;
        }
        markGuidedProductOwned();
        window.location.href = `/order/status/${state.orderId}?paid=1`;
        return;
      }
      const url = await startOrderCheckout(state.orderId);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось начать оплату");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card
      padding="lg"
      hover={false}
      className="flex h-full min-h-0 flex-col border-emerald-500/25 bg-genesis-panel/60"
    >
      <SpringIn>
        <button
          type="button"
          onClick={onBack}
          className="mb-4 self-start text-xs text-genesis-muted transition hover:text-white"
        >
          ← Назад
        </button>
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">
          Оплата
        </p>
        <h2 className="mt-3 text-xl font-bold text-white sm:text-2xl">
          {state.companyName.trim()}
        </h2>
        <p className="mt-2 text-sm text-genesis-muted">
          Заказ № {state.orderId}. Справа — тот же Product; оплата передаёт вам права на него.
        </p>
      </SpringIn>

      <div className="mt-5 rounded-xl border border-white/10 bg-white/5 px-4 py-4">
        <p className="text-xs text-genesis-muted">К оплате</p>
        <p className="mt-1 text-3xl font-bold tabular-nums text-white">{priceDisplay}</p>
      </div>

      {paymentReady ? (
        <SpringPressable
          type="button"
          disabled={busy}
          onClick={() => void pay()}
          className="mt-5 w-full rounded-xl bg-emerald-600 py-3.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? "Переход к оплате…" : `Оплатить ${priceDisplay}`}
        </SpringPressable>
      ) : (
        <p className="mt-5 rounded-xl border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-100">
          Оплата скоро будет доступна здесь. Мы свяжемся с вами на {state.clientEmail}.
        </p>
      )}

      {error ? (
        <p className="mt-2 text-xs text-rose-300" role="alert">
          {error}
        </p>
      ) : null}

      <HelpLink onNeedHelp={onNeedHelp} />
    </Card>
  );
}
