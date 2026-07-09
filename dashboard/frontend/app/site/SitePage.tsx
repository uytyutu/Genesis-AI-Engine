"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
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
    a: `Обычно от нескольких дней — точный срок зависит от вашего проекта. ${ASSISTANT_NAME} назовёт его после короткого разговора.`,
  },
  {
    q: "Нужно ли что-то техническое от меня?",
    a: `Нет. Достаточно рассказать о задаче простыми словами — ${ASSISTANT_NAME} сделает остальное.`,
  },
  {
    q: "Как происходит оплата?",
    a: "Сначала вы видите ориентировочную стоимость в диалоге. Оплата — только когда вы согласны оформить заказ.",
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
  const [services, setServices] = useState<ServiceCatalogItem[]>([]);
  const [chatActive, setChatActive] = useState(false);

  useEffect(() => {
    void fetchPricingDisplay().then((data) => {
      const items = (data.service_categories ?? []).flatMap((c) => c.items);
      setServices(items.slice(0, 3));
    });
  }, []);

  return (
    <PublicPageShell hideChrome={false}>
      <GenesisChatErrorBoundary>
        <GenesisConcierge onConversationActive={setChatActive} />
      </GenesisChatErrorBoundary>

      {!chatActive && (
        <>
          <details className="group mt-10 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/40 open:bg-genesis-panel/60">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-semibold marker:content-none sm:px-6">
              <span className="flex items-center justify-between gap-2">
                {t("aboutTitle", { brand: BRAND_NAME })}
                <span className="text-genesis-muted transition group-open:rotate-180">▼</span>
              </span>
            </summary>
            <div className="space-y-4 border-t border-genesis-border-subtle px-5 py-5 text-sm text-genesis-muted sm:px-6">
              <p>
                {t("aboutBody", { brand: BRAND_NAME, assistant: ASSISTANT_NAME })}
              </p>
              <button
                type="button"
                onClick={focusGenesisChat}
                className="text-sm font-medium text-genesis-accent hover:underline"
              >
                {t("startChat")}
              </button>
            </div>
          </details>

          <details className="group mt-4 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/40">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-semibold marker:content-none sm:px-6">
              <span className="flex items-center justify-between gap-2">
                {tCommon("nav.services")}
                <span className="text-genesis-muted transition group-open:rotate-180">▼</span>
              </span>
            </summary>
            <div className="border-t border-genesis-border-subtle p-5 sm:p-6">
              <p className="mb-4 text-sm text-genesis-muted">
                {t("servicesIntro", { brand: BRAND_NAME })}
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                {services.map((item, i) => (
                  <Card key={item.id} glow={i === 0 && item.available} padding="md">
                    <p className="font-semibold">{item.name}</p>
                    <p className="mt-2 text-2xl font-bold tabular-nums text-genesis-accent">
                      {item.price_label}
                    </p>
                    {item.timeline && (
                      <p className="mt-1 text-xs text-genesis-muted">Срок: {item.timeline}</p>
                    )}
                    <p className="mt-2 text-xs text-genesis-muted line-clamp-3">{item.description}</p>
                  </Card>
                ))}
              </div>
              <ButtonLink href="/services" variant="ghost" size="sm" className="mt-4">
                Весь каталог услуг →
              </ButtonLink>
            </div>
          </details>

          <details className="group mt-4 rounded-2xl border border-genesis-border-subtle bg-genesis-panel/40">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-semibold marker:content-none sm:px-6">
              <span className="flex items-center justify-between gap-2">
                {t("faqTitle")}
                <span className="text-genesis-muted transition group-open:rotate-180">▼</span>
              </span>
            </summary>
            <div className="border-t border-genesis-border-subtle p-5 sm:p-6">
              <FaqList items={FAQ} />
            </div>
          </details>
        </>
      )}
    </PublicPageShell>
  );
}
