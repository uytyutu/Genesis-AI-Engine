"use client";

import { PublicPageShell } from "../components/PublicPageShell";
import { Badge, ButtonLink, Card } from "../components/ui";
import { ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME } from "../lib/publicBrand";
import { PUBLIC_LANDING_MIN_EUR } from "../lib/pricingFallback";

/** Legacy /products URL — honest Mission 1 availability (Studio not sold yet). */
export default function ProductsPage() {
  return (
    <PublicPageShell>
      <div className="mx-auto max-w-2xl py-4 text-center">
        <Badge variant="outline">{BRAND_NAME}</Badge>
        <h1 className="mt-4 text-3xl font-bold">Что доступно сейчас</h1>
        <p className="mt-3 text-genesis-muted">
          {STUDIO_NAME} и подписки пока <strong className="text-white">нельзя купить онлайн</strong>.
          Ниже — то, что работает сегодня.
        </p>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <Card glow padding="lg" className="text-left">
          <p className="text-sm font-semibold text-emerald-300">Free</p>
          <p className="mt-2 text-lg font-bold">Познакомиться с {ASSISTANT_NAME}</p>
          <p className="mt-2 text-sm text-genesis-muted">
            Обсудите идею, получите ориентир по цене — без оплаты.
          </p>
          <ButtonLink href="/site" variant="primary" size="md" className="mt-5">
            Начать работу →
          </ButtonLink>
        </Card>

        <Card glow padding="lg" className="text-left border-emerald-500/30">
          <p className="text-sm font-semibold text-emerald-300">Create</p>
          <p className="mt-2 text-lg font-bold">Лендинг под ключ</p>
          <p className="mt-2 text-sm text-genesis-muted">
            Пакеты {PUBLIC_LANDING_MIN_EUR} / 650 / 1200 € — как на форме заказа.
          </p>
          <ButtonLink href="/order" variant="success" size="md" className="mt-5">
            Заказать →
          </ButtonLink>
        </Card>
      </div>

      <Card className="mt-8 border-amber-500/25 bg-amber-950/15" padding="md">
        <p className="text-sm text-genesis-muted">
          <strong className="text-amber-100">{STUDIO_NAME}</strong> (среда для проектов, подписка) — в разработке.
          Мы сообщим, когда можно будет подключить. Сейчас — работа с Vector и заказ лендинга.
        </p>
      </Card>
    </PublicPageShell>
  );
}
