"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
import {
  PublicFunnelSteps,
  PublicIntroTeaser,
} from "../components/navigation/PublicIntroTeaser";
import { PublicFunnelFooter } from "../components/navigation/PublicFunnelFooter";
import { FaqList } from "../components/FaqList";
import { Card, ButtonLink } from "../components/ui";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import {
  fetchPricingDisplay,
  type ServiceCatalogItem,
} from "../lib/pricingApi";

const FAQ = [
  {
    q: "Сколько ждать готовый сайт?",
    a: `Обычно от нескольких дней — точный срок зависит от вашего проекта. ${ASSISTANT_NAME} назовёт его после короткой консультации.`,
  },
  {
    q: "Нужно ли что-то техническое от меня?",
    a: `Нет. Достаточно рассказать о задаче простыми словами — ${ASSISTANT_NAME} доведёт работу до результата.`,
  },
  {
    q: "Как происходит оплата?",
    a: "Сначала вы видите ориентировочную стоимость. Оплата — когда согласны оформить заказ.",
  },
  {
    q: "Что если мне нужны правки?",
    a: "В услугах под ключ предусмотрены раунды правок. Подробности — когда подберём решение под вашу задачу.",
  },
];

function focusGenesisChat() {
  window.dispatchEvent(new Event("genesis:focus-chat"));
}

export function SitePage() {
  const { t } = useTranslation("site");
  const { t: tCommon } = useTranslation("common");
  const searchParams = useSearchParams();
  const vectorView = searchParams.get("view") === "vector";
  const [services, setServices] = useState<ServiceCatalogItem[]>([]);

  useEffect(() => {
    void fetchPricingDisplay().then((data) => {
      const items = (data.service_categories ?? []).flatMap((c) => c.items);
      setServices(items.slice(0, 3));
    });
  }, []);

  return (
    <PublicPageShell>
      {!vectorView && (
        <div className="mb-6">
          <PublicFunnelSteps activeId="home" />
        </div>
      )}

      <div
        className={`grid min-h-[min(80dvh,52rem)] gap-4 lg:grid-cols-[minmax(380px,62%)_minmax(0,1fr)] lg:gap-6 ${
          vectorView ? "max-lg:grid-cols-1" : ""
        }`}
      >
        <section
          id="vector-panel"
          className={`order-first flex min-h-[min(72dvh,44rem)] min-w-0 flex-col lg:min-h-0 ${
            vectorView ? "" : "max-lg:order-first"
          }`}
          aria-label={tCommon("nav.vector")}
        >
          <GenesisChatErrorBoundary publicMode>
            <GenesisConcierge hubMode />
          </GenesisChatErrorBoundary>
        </section>

        <section
          className={`min-h-0 ${vectorView ? "max-lg:hidden lg:hidden" : ""}`}
          aria-label="Знакомство с Virtus Core"
        >
          <PublicIntroTeaser onTryVector={focusGenesisChat} />
        </section>
      </div>

      {!vectorView && (
        <>
          <section className="mt-10 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/50 p-6 sm:p-8">
            <h2 className="text-lg font-semibold">{t("aboutTitle", { brand: BRAND_NAME })}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-genesis-muted">
              {t("aboutBody", { brand: BRAND_NAME, assistant: ASSISTANT_NAME })}
            </p>
            <ButtonLink href="/site?view=vector" variant="secondary" size="sm" className="mt-4">
              Поговорить с {ASSISTANT_NAME} →
            </ButtonLink>
          </section>

          <section className="mt-6 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/40 p-6 sm:p-8">
            <h2 className="text-lg font-semibold">{tCommon("nav.services")}</h2>
            <p className="mt-2 text-sm text-genesis-muted">
              {t("servicesIntro", { brand: BRAND_NAME, assistant: ASSISTANT_NAME })}
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {services.map((item, i) => (
                <Card key={item.id} glow={i === 0 && item.available} padding="md">
                  <p className="font-semibold">{item.name}</p>
                  <p className="mt-2 text-2xl font-bold tabular-nums text-genesis-accent">
                    {item.price_label}
                  </p>
                  {item.timeline ? (
                    <p className="mt-1 text-xs text-genesis-muted">Срок: {item.timeline}</p>
                  ) : null}
                  <p className="mt-2 text-xs text-genesis-muted line-clamp-3">{item.description}</p>
                </Card>
              ))}
            </div>
            <ButtonLink href="/services" variant="primary" size="sm" className="mt-5">
              {t("hubViewServices")} →
            </ButtonLink>
          </section>

          <section className="mt-6 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/40 p-6 sm:p-8">
            <h2 className="text-lg font-semibold">{t("faqTitle")}</h2>
            <div className="mt-4">
              <FaqList items={FAQ} />
            </div>
          </section>

          <section
            id="download"
            className="mt-10 scroll-mt-24 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/25 to-genesis-panel p-6 sm:p-8"
          >
            <h2 className="text-lg font-semibold">Создайте свою цифровую компанию</h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-genesis-muted">
              Вы уже познакомились с {ASSISTANT_NAME} и увидели, как работает {BRAND_NAME}.
              Следующий шаг — установить приложение и открыть <strong className="text-white">свою компанию</strong>:
              проекты, память и полный Vector без ограничений витрины.
            </p>
            <p className="mt-4 text-sm text-emerald-300/90">
              Запустите <strong>Genesis.exe</strong> с рабочего стола — это Virtus Core для ежедневной работы.
            </p>
            <p className="mt-2 text-xs text-genesis-muted">
              Сайт знакомит. Приложение — где вы живёте с Vector каждый день.
            </p>
          </section>

          <Suspense fallback={null}>
            <PublicFunnelFooter />
          </Suspense>
        </>
      )}

      {vectorView && (
        <div className="mt-6">
          <Suspense fallback={null}>
            <PublicFunnelFooter />
          </Suspense>
        </div>
      )}
    </PublicPageShell>
  );
}
